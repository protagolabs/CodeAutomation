import os
import sys
import uuid
import json

import boto3
import subprocess

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

    def __init__(self, job_id, entry_point, arguments):
        self.job_id = job_id
        self.entry_point = entry_point
        self.arguments = arguments

    def generate_bash_file(self):
        entry_point_sh_name = f'{self.job_id}.sh'
        with open(entry_point_sh_name, 'w') as rsh:
            rsh.write(f"\#! /bin/bash \n python {self.entry_point} {self.arguments}\n")

    def generate_py_file(self):
        target_py_file_name = f'{self.job_id}.py'
        with open(target_py_file_name, 'w') as f:
            f.write(f'import subprocess\n')
            f.write(f'import os\n')
            f.write(f'entry_point_sh_name = {self.job_id}.sh\n')
            #f.write(f"ret = subprocess.run('bash {self.job_id}.sh', shell=True, capture_output=True, encoding='utf-8')\n")
            f.write(f"os.system('bash {self.job_id}.sh)\n")

    def post_process(self, code_dir):
        ret = subprocess.run(f'mv {self.job_id}.sh {self.job_id}.py {code_dir}', shell=True, capture_output=True, encoding='utf-8')


class CodeBuilder:
    def __init__(self, job_id, s3_path, entry_point, arguments) -> None:
        self.job_id = job_id
        self.s3_bucket = f'protagolabs-netmind-job-model-code-{domain}'
        self.s3_key = s3_path
        self.entry_point_file = entry_point
        self.code_generator_impl = CodeGenerator(job_id, entry_point, arguments)

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


    def build(self):
        compress_dir, code_dir = self.download_code()
        if not compress_dir or not code_dir:
            raise Exception(f'download code from {self.s3_bucket}:{self.s3_key} failed')

        #wrap entry point
        self.code_generator_impl.generate_bash_file()
        self.code_generator_impl.generate_py_file()
        self.code_generator_impl.post_process(code_dir)

        compile_path = os.path.join(code_dir, '*')
        output_file = os.path.join('/tmp', 'binary_run_file')


        if not compress_dir and not code_dir:
            raise Exception(f'get code from {self.s3_bucket}:{self.s3_key} failed')

        #entry_point = os.path.join(code_dir, self.entry_point_file)

        import datetime
        starttime = datetime.datetime.now()
        entry_point_wrap_file_path = os.path.join(code_dir, f'{self.job_id}.py')
        command_compile_binary_package = f"python -m nuitka --nofollow-imports {entry_point_wrap_file_path}" \
                                         f" --include-plugin-files={compile_path} " \
                                         f"--output-filename={output_file} --output-dir=/tmp"


        ret = subprocess.run(command_compile_binary_package, shell=True, capture_output=False, encoding='utf-8', timeout=50, check=True)
        endtime = datetime.datetime.now()
        print(f'command cost : {endtime - starttime}')

        validate_status(ret.returncode, command_compile_binary_package)
        logger.info(f'execute command {command_compile_binary_package} finish')
        logger.info(ret)

        with open(output_file, 'rb') as f:
            binary_key = os.path.join(self.s3_key.split('/')[0], 'binary_run_file')

            s3_client.upload_fileobj(f, self.s3_bucket, binary_key)

        ret = subprocess.run(f"rm -rf {compress_dir}", shell=True, capture_output=True, encoding='utf-8')
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
    except Exception:
        event_msg = f"compile by event {json_body} failed"
        job_event_dao.quick_insert(job_id, 'failed', EventLevel.ERROR, event_msg)


