import datetime
import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import uuid

import boto3
from tool import lambda_invoke, uncompress_code

sys.path.append("..")
from dynamodb.job_event import EventLevel, job_event_dao

logger = logging.getLogger(__name__)


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if hasattr(record, "origin_created"):
            record.created = record.origin_created
            record.msecs = (record.created - int(record.created)) * 1000

        if record.levelno != logging.INFO or os.getenv(
            "NETMIND_ALWAYS_LOG_CALLER", True
        ):
            if not hasattr(record, "caller"):
                record.caller = f"{record.name}.{record.funcName}:{record.lineno}"
            record.caller_block = f" [{record.caller}]"
        else:
            record.caller_block = ""

        return super().format(record)


formatter = CustomFormatter(
    fmt="{asctime}.{msecs:03.0f} [{levelname}]{caller_block} {message}",
    style="{",
    datefmt="%b %d %H:%M:%S",
)
_default_handler = logging.StreamHandler()
_default_handler.setFormatter(formatter)
logger.addHandler(_default_handler)
logger.propagate = False
logger.setLevel(os.getenv("NETMIND_LOGLEVEL", "INFO"))

region = os.getenv("REGION", "us-west-2")
domain = os.getenv("DOMAIN", "test")

s3_client = boto3.client("s3", region_name=region)

LAMBDA_PREPARE_COMPLETE = f"arn:aws:lambda:us-west-2:134622832812:function:netmind-services-job-management-{domain}-trainPreparationComplete"


def validate_status(status, command_rsa_build_client):
    if status:
        raise Exception(f"execute {command_rsa_build_client} failed")


def validate_path(path):
    if os.path.exists(path):
        raise FileExistsError(f"path {path} already exists")


class CodeBuilder:
    def __init__(self, job_id, s3_path, entry_point, arguments) -> None:
        self.job_id = job_id
        self.s3_bucket = f"protagolabs-netmind-job-model-code-{domain}"
        if s3_path.endswith("ipynb"):
            s3_path = "".join([s3_path.split(".")[0], ".py"])
        self.s3_key = s3_path
        if entry_point.endswith(".ipynb"):
            entry_point = "".join([entry_point.split(".")[0], ".py"])
        self.entry_point_file = entry_point
        self.arguments = arguments

    def handle_entry_point(self, code_dir):
        entry_point_file = os.path.join(code_dir, self.entry_point_file)
        argument_list = self.arguments.split(" ")
        str_argument_list = [self.entry_point_file]
        for argument in argument_list:
            if len(argument) > 0:
                str_argument_list.append(str(argument))
        command_argv = f"sys.argv = {str_argument_list}"
        logger.info(f"command_argv {command_argv}")

        with open(entry_point_file, "r") as f:
            lines = f.readlines()

        with open(entry_point_file, "w") as f:
            f.write("import sys\n")
            f.write(f"{command_argv}\n")
            for line in lines:
                f.write(line)

    def download_code(self):

        try:
            logger.info(f"{self.s3_bucket} :  {self.s3_key}")
            temp_dir = "/tmp/" + str(uuid.uuid4())
            os.makedirs(temp_dir, exist_ok=True)

            file_name = self.s3_key.split("/")[1]
            download_file_dir = os.path.join("/tmp", "download_file")
            os.makedirs(download_file_dir, exist_ok=True)
            write_obj = os.path.join(download_file_dir, file_name)

            logger.info(f"download {self.s3_bucket}, {self.s3_key} to {write_obj}")
            s3_client.download_file(self.s3_bucket, self.s3_key, write_obj)

            final_file_name = uncompress_code(self.s3_key, write_obj, temp_dir)
            if final_file_name:
                self.entry_point_file = final_file_name

            logger.info(f"uncompress to {temp_dir}")
            output = [
                directory
                for directory in os.listdir(temp_dir)
                if os.path.isdir(os.path.join(temp_dir, directory))
            ]
            if len(output) >= 2:
                if "__MACOSX" in output:
                    del output[output.index("__MACOSX")]

            file_list = os.listdir(temp_dir)
            file_list = set(filter(lambda x: x.endswith(".py"), file_list))
            ipynb_list = set(filter(lambda x: x.endswith(".ipynb"), file_list))
            if len(ipynb_list) == 0 and len(file_list) == 0:
                file_dir = output[0] if len(output) == 1 else None
                if file_dir:
                    source_dir = os.path.join(temp_dir, file_dir)
                    file_dir = file_dir.replace(" ", "")
                    replaced_file_dir = os.path.join(temp_dir, file_dir)
                    shutil.move(source_dir, replaced_file_dir)

                    temp_dir = os.path.join(temp_dir, file_dir)

            compress_dir = temp_dir

            logger.info(f"code path : {temp_dir}")
            code_dir = temp_dir

            requiment_path = os.path.join(code_dir, "requirements.txt")
            logger.info(f"requiment_path: {requiment_path}")

            if os.path.exists(requiment_path):
                with open(requiment_path, "rb") as f:
                    requiments_key = os.path.join(
                        self.s3_key.split("/")[0], "requirements.txt"
                    )
                    s3_client.upload_fileobj(f, self.s3_bucket, requiments_key)

        except Exception as e:
            logger.exception(e)
            return None, None
        finally:
            if os.path.exists(download_file_dir):
                shutil.rmtree(download_file_dir)

        return compress_dir, code_dir

    def __execute_command(self, command):
        ret = subprocess.run(
            command,
            shell=True,
            capture_output=False,
            encoding="utf-8",
            timeout=50,
            check=True,
        )
        validate_status(ret.returncode, command)
        return

    def __add_package_name(self, destination_dir):
        command = ""
        add_package_command = "  --follow-import-to="
        glob_list = glob.glob(f"{destination_dir}/*/**/", recursive=True)
        for item in glob_list:
            base_name = item.split("/")[-2]
            if base_name.startswith("__"):
                continue
            # get all package directory and added on nuitka command
            package_name = (
                item.replace(destination_dir, "").strip("/").replace("/", ".")
            )
            command += add_package_command + package_name
        return command

    def build(self):
        compress_dir, code_dir = self.download_code()
        if not compress_dir or not code_dir:
            raise Exception(f"download code from {self.s3_bucket}:{self.s3_key} failed")

        self.handle_entry_point(code_dir)

        compile_path = os.path.join(code_dir, "*")
        if not compress_dir and not code_dir:
            raise Exception(f"get code from {self.s3_bucket}:{self.s3_key} failed")

        starttime = datetime.datetime.now()

        binary_run_file = os.path.join("/tmp", "binary_run_file")
        command_compile_binary_package = (
            f"python -m nuitka {os.path.join(code_dir, f'{self.entry_point_file}')} "
            f" --include-plugin-files={compile_path} "
            f"--output-filename={binary_run_file} --output-dir=/tmp --remove-output"
        )
        command_compile_binary_package += self.__add_package_name(code_dir)

        self.__execute_command(command_compile_binary_package)
        logger.info(f"execute command {command_compile_binary_package} finish")

        endtime = datetime.datetime.now()
        logger.info(f"command cost : {endtime - starttime}")

        with open(binary_run_file, "rb") as f_binary:

            binary_key = os.path.join(self.s3_key.split("/")[0], "binary_run_file")
            s3_client.upload_fileobj(f_binary, self.s3_bucket, binary_key)

        # handle code_dir, delete all py file and upload to s3
        for file in glob.glob(f"{code_dir}/**/*.py", recursive=True):
            os.system(f"rm {file}")
        resource_package_name = "/tmp/resource.tar.gz"
        code_dir_parent_dir = os.path.dirname(code_dir)
        code_dir_base_dir = os.path.basename(code_dir)
        os.system(
            f"cd {code_dir_parent_dir} && tar czvf {resource_package_name} {code_dir_base_dir} && cd -"
        )
        with open(resource_package_name, "rb") as f_resource:
            resource_package_key = os.path.join(
                self.s3_key.split("/")[0], "resource.tar.gz"
            )
            logger.info(
                f"upload {resource_package_name} to {self.s3_bucket}:{resource_package_key}"
            )
            s3_client.upload_fileobj(f_resource, self.s3_bucket, resource_package_key)

        # clean unused directory
        subprocess.run(
            f"rm -rf {compress_dir} ", shell=True, capture_output=True, encoding="utf-8"
        )
        logger.info(f"remove_dir : {compress_dir}")
        subprocess.run(
            f"rm  {resource_package_name} ",
            shell=True,
            capture_output=True,
            encoding="utf-8",
        )
        logger.info(f"remove resource package  : {resource_package_name}")

        param = {"job_id": self.job_id, "success": True}
        logger.info(f"send {param} to {LAMBDA_PREPARE_COMPLETE}")
        lambda_invoke(LAMBDA_PREPARE_COMPLETE, param)


def handler(event, context):
    logger.info(f"receive event: {event}, type: {type(event)}")
    if "Records" not in event:
        raise ValueError(f"invalid format {event}")

    message_body = event["Records"][0]["body"]
    # json_body = message_body
    json_body = json.loads(message_body)
    field_list = ["s3_path", "entry_point", "job_id", "train_arguments"]

    for field in field_list:
        if field not in json_body:
            raise ValueError(f"invalid format {event}")
    job_id = json_body["job_id"]
    s3_path = json_body["s3_path"]
    entry_point = json_body["entry_point"]
    train_arguments = json_body["train_arguments"]
    try:
        build = CodeBuilder(job_id, s3_path, entry_point, train_arguments)
        build.build()
    except Exception as e:
        logger.error(str(e))
        event_msg = "code build procedure failed."
        import traceback

        traceback.print_exc()

        job_event_dao.quick_insert(job_id, "failed", EventLevel.ERROR, event_msg)
        param = {"job_id": job_id, "success": False}
        logger.info(f"send {param} to {LAMBDA_PREPARE_COMPLETE}")
        lambda_invoke(LAMBDA_PREPARE_COMPLETE, param)


if __name__ == "__main__":
    event = {
        "Records": [
            {
                "messageId": "05950022-edbb-4468-bcca-8e0dee6d6542",
                "receiptHandle": "AQEBxRUrmYkA00cSxN5tkNQQ48TDpdUxIauIBJEiBSUhw0PwrZkTauy4G3qbGq9umnGQSRAwmUBlu4KM89FLz7c+0b8CtwRzSZD3lhOTnBNnhe541/nI2XV6o4SBaVX4pudtRl2bSMbItjS2NG8N+KkZQlEITNh9NJIX0iSqAaG5jwTWzS6T2xFb84asfHb2lw/iDzmJ6jR6EQIF3HK6pEc3DUoRW0Mkl+PocVlcZmbAIuNqRJZ64xetA0u0RhuOqVXthBF9aJmlGf5MXXzFwR65hdeDKLce69N9ipSuOHBIM9vdOVb+8Uyrp2Pyi8I8QB760RYUDSnCXtB3P1tO28dc9hT+dUTIrfKA0wW09bqxHIxgOn18pUBPbRsDfKoDFM7uaI3IL8BrYu8DKS0DmGuex7g7aeSlLhU+5qcWfrmhPC0=",
                "body": '{"job_id": "4469f85c-a64f-4a7c-9a49-9c811197fbbf", '
                '"s3_path": "e0ab34e7-0cbc-425d-9ed6-409f60ecaa6d/deep_learning_models.zip", '
                '"entry_point": "bert_qa_preprocess_and_finetune_script.py", '
                '"train_arguments": ""}',
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1692947727248",
                    "SenderId": "AROAR6WBFNCWKFQGHTV7Y:netmind-services-job-management-test-jobCommon",
                    "ApproximateFirstReceiveTimestamp": "1692947732248",
                },
                "messageAttributes": {},
                "md5OfBody": "e4ed6681fe1d9b6f9d7a78200c83ff0f",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-west-2:134622832812:netmind-code-compile-test-queue",
                "awsRegion": "us-west-2",
            }
        ]
    }

    event = {
        "Records": [
            {
                "messageId": "0f53b920-eec0-4c2e-8899-a196194a428b",
                "receiptHandle": "AQEBz1khCgIKXe9S2AKxqtSaMxFEdgKJXEUad+gOtE9Uupompag7R/yJKOCpBgHujNzeJwtWVn2rssfOD/4KWuNLFPyoOlRYLsMv/dzD8RHPR4IcS5xxAxv49oy8MUlGTmdJAxt/tz0TjkADF6dZEO3AUPw6j5Q8W/FBYgnigkMInicwtp5o4PCzhEyfTEA8MlJ2TYH9DVfsdwNKuxl/a1k8rb6YE94sSKBG4Wy9yObbo/RS36Qi5yh7f/QnN/xNW/EnowusvZNvfqteF4O8kvOgsjYjTO/IGWEjrFYjt1Gebq9KqP/+eke9AD85YS6OEMQY2K7TFRtBnzzRn1LH0yIIQgGMTTY2ayvPau0SRyvQeYBzZVH5/xNmYukzxvLZzyN/l3EYc4Xqad1r+5m2e3xDmj8xo6hGc7KjU7vHDSgvtjg=",
                "body": '{"job_id": "867600c9-24b5-4c66-920e-b2a61dd1fccf", "s3_path": "3ecc3893-748b-4161-a484-8561535e7960/torch_resnet_custom_ddp_automated.tar.gz", "entry_point": "train_dist.py", "train_arguments": "--data /netmind_train/datasets/867600c9-24b5-4c66-920e-b2a61dd1fccf"}',
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1694750022912",
                    "SenderId": "AROAR6WBFNCWKFQGHTV7Y:netmind-services-job-management-test-jobCommon",
                    "ApproximateFirstReceiveTimestamp": "1694750027913",
                },
                "messageAttributes": {},
                "md5OfBody": "e65f54f393b6c58c98e1b658034deae3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-west-2:134622832812:netmind-code-compile-test-queue",
                "awsRegion": "us-west-2",
            }
        ]
    }
    handler(event, None)
