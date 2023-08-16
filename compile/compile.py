import os
import sys
import uuid
import json

import boto3
import subprocess
import datetime

import logging
from tool import uncompress_code, lambda_invoke
sys.path.append("..")
from dynamodb.job_event import job_event_dao, EventLevel

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.propagate = False
logger.setLevel(os.getenv("NETMIND_LOGLEVEL", "INFO"))

region = os.getenv("REGION", "us-west-2")
domain = os.getenv("DOMAIN", "dev")

s3_client = boto3.client('s3', region_name = region)

LAMBDA_PREPARE_COMPLETE = f'arn:aws:lambda:us-west-2:134622832812:function:netmind-services-job-management-{domain}-trainPreparationComplete'

def validate_status(status, command_rsa_build_client):
    if status:
        raise Exception(f'execute {command_rsa_build_client} failed')

def validate_path(path):
    if os.path.exists(path):
        raise FileExistsError(f'path {path} already exists')


class CodeGenerator(object):

    def __init__(self, job_id, arguments, code_dir):
        self.job_id = job_id
        self.code_dir = code_dir
        self.target_py_file_name = os.path.join(self.code_dir, f'{self.job_id}.py')
        self.arguments = arguments

    """
    def generate_bash_file(self):
        with open(self.entry_point_sh_name, 'w') as f:

            #f.write("#! /bin/bash \n python {self.entry_point} {self.arguments}\n")
            f.write(f"#! /bin/bash \npython {self.entry_point} {self.arguments}\n")
    """

    def generate_py_file(self, unwrapped_binary_file):
        with open(self.target_py_file_name, 'w') as f:
            f.write(f'import os\n')
            f.write(f"os.system('./unwrapped_binary_file {self.arguments}')\n")




class CodeBuilder:
    def __init__(self, job_id, s3_path, entry_point, arguments) -> None:
        self.job_id = job_id
        self.s3_bucket = f'protagolabs-netmind-job-model-code-{domain}'
        self.s3_key = s3_path
        self.entry_point_file = entry_point
        self.arguments = arguments

    def download_code(self):
        compress_dir = ''
        code_dir = ''
        write_obj = ''
        try:
            logger.info(f'{self.s3_bucket} :  {self.s3_key}')

            file_name = self.s3_key.split('/')[1]
            write_obj = os.path.join('/tmp', file_name)

            logger.info(f'download {self.s3_bucket}, {self.s3_key}')
            s3_client.download_file( self.s3_bucket, self.s3_key, write_obj)


            temp_dir = "/tmp/" + str(uuid.uuid4())
            os.makedirs(temp_dir, exist_ok=True)
            uncompress_code(write_obj, temp_dir)
            logger.info(f'uncompress to {temp_dir}')
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
            if len(file_list) == 0:
                file_dir = output[0] if len(output) == 1 else ""
                temp_dir = os.path.join(temp_dir, file_dir)

            compress_dir = temp_dir

            logger.info(f'code path : {temp_dir}')
            code_dir = temp_dir

            requiment_path = os.path.join(code_dir, 'requirements.txt')
            logger.info(f'requiment_path: {requiment_path}')

            if os.path.exists(requiment_path):
                with open(requiment_path, 'rb') as f:
                    requiments_key = os.path.join(self.s3_key.split('/')[0], 'requirements.txt')
                    s3_client.upload_fileobj(f, self.s3_bucket, requiments_key)

        except Exception as e:
            logger.exception(e)
            return None, None
        finally:
            ret = subprocess.run(f"rm -rf {write_obj}", shell=True, capture_output=True, encoding='utf-8')
            logger.info(f'remove file : {write_obj}')
            pass

        return compress_dir, code_dir


    def __execute_command(self, command):
        ret = subprocess.run(command, shell=True, capture_output=False,
                             encoding='utf-8', timeout=50, check=True)
        validate_status(ret.returncode, command)
        return

    def build(self):
        compress_dir, code_dir = self.download_code()
        if not compress_dir or not code_dir:
            raise Exception(f'download code from {self.s3_bucket}:{self.s3_key} failed')


        compile_path = os.path.join(code_dir, '*')
        unwrapped_binary_file = os.path.join('/tmp','unwrapped_binary_file')
        if not compress_dir and not code_dir:
            raise Exception(f'get code from {self.s3_bucket}:{self.s3_key} failed')

        #entry_point = os.path.join(code_dir, self.entry_point_file)

        starttime = datetime.datetime.now()
        entry_point_file = os.path.join(code_dir, self.entry_point_file)
        command_compile_unwrapped_binary_package = f"python -m nuitka --nofollow-imports {entry_point_file}" \
                                         f" --include-plugin-files={compile_path} " \
                                         f"--output-filename={unwrapped_binary_file} --output-dir=/tmp --remove-output"

        self.__execute_command(command_compile_unwrapped_binary_package)
        logger.info(f'execute command {command_compile_unwrapped_binary_package} finish')

        # wrap entry point
        code_generator_impl = CodeGenerator(self.job_id, self.arguments, code_dir)
        code_generator_impl.generate_py_file(unwrapped_binary_file)

        binary_run_file = os.path.join('/tmp','binary_run_file')
        command_compile_binary_package = f"python -m nuitka {os.path.join(code_dir, f'{self.job_id}.py')} " \
                                                   f"--output-filename={binary_run_file} --output-dir=/tmp --remove-output"
        self.__execute_command(command_compile_binary_package)
        logger.info(f'execute command {command_compile_binary_package} finish')

        endtime = datetime.datetime.now()
        print(f'command cost : {endtime - starttime}')




        with open(unwrapped_binary_file, 'rb') as f_unwrapped, open(binary_run_file, 'rb') as f_binary:
            unwrapped_key = os.path.join(self.s3_key.split('/')[0], 'unwrapped_binary_file')
            s3_client.upload_fileobj(f_unwrapped, self.s3_bucket, unwrapped_key)

            binary_key = os.path.join(self.s3_key.split('/')[0], 'binary_run_file')
            s3_client.upload_fileobj(f_binary, self.s3_bucket, binary_key)

        ret = subprocess.run(f"rm -rf {compress_dir} ", shell=True, capture_output=True, encoding='utf-8')
        logger.info(f'remove_dir : {compress_dir}')
        param = {'job_id': self.job_id}
        logger.info(f'send {param} to {LAMBDA_PREPARE_COMPLETE}')
        lambda_invoke(LAMBDA_PREPARE_COMPLETE,  param)


def handler(event, context):
    logger.info(f'receive event: {event}, type: {type(event)}')
    if "Records" not in event:
        raise ValueError(f'invalid format {event}')

    message_body = event["Records"][0]["body"]


    json_body = json.loads(message_body)
    field_list = ['s3_path', 'entry_point', 'job_id', 'train_arguments']

    for field in field_list:
        if field not in json_body:
            raise ValueError(f'invalid format {event}')
    job_id = json_body['job_id']
    s3_path = json_body['s3_path']
    entry_point = json_body['entry_point']
    train_arguments = json_body['train_arguments']
    try:
        build = CodeBuilder(job_id, s3_path, entry_point, train_arguments)
        build.build()
    except Exception as e:
        #event_msg = f"compile by event {json_body} failed"
        event_msg = str(e)
        print(event_msg)
        import  traceback
        traceback.print_exc()

        job_event_dao.quick_insert(job_id, 'failed', EventLevel.ERROR, event_msg)

"""
if __name__ == '__main__':
    event = {
        'Records': [{'body': {
                'job_id': '8c2eba07-8d86-4f46-80f8-da0d76b35adc',
                's3_path': 'a45babc9-0495-4356-a8c2-27cea80666a7/tf-resnet-custom-automated.tar.gz',
                'entry_point': 'train_netmind.py',
                'train_arguments': '--model_name_or_path=resnet50'
        }}]
}
    handler(event, None)
"""

