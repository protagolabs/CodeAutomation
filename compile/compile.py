import os
import uuid

import boto3
import subprocess
import datetime


import time
import logging
from tool import uncompress_code
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.propagate = False
logger.setLevel(os.getenv("NETMIND_LOGLEVEL", "INFO"))

region = os.getenv("REGION", "us-west-2")
domain = os.getenv("DOMAIN", "dev")

s3_client = boto3.client('s3', region_name = region)

def validate_status(status, command_rsa_build_client):
    if status:
        raise Exception(f'execute {command_rsa_build_client} failed')

def validate_path(path):
    if os.path.exists(path):
        raise FileExistsError(f'path {path} already exists')

class CodeBuilder:
    def __init__(self, s3_path, entry_point) -> None:
        self.s3_bucket = f'protagolabs-netmind-job-model-code-{domain}'
        self.s3_key = s3_path
        self.entry_point_file = entry_point

    def download_code(self):
        compress_dir = ''
        code_dir = ''
        write_obj = ''
        try:
            logger.info(f'{self.s3_bucket} :  {self.s3_key}')

            file_name = self.s3_key.split('/')[1]
            write_obj = os.path.join('/tmp', file_name)

            s3_client.download_file( self.s3_bucket, self.s3_key, write_obj)
            logger.info(f'download {self.s3_bucket}, {self.s3_key}')


            temp_dir = "/tmp/" + str(uuid.uuid4())
            os.makedirs(temp_dir, exist_ok=True)
            uncompress_code(write_obj, temp_dir)
            logger.info(f'uncompress to {temp_dir}')
            compress_dir = temp_dir

            items = os.listdir(temp_dir)
            logger.info(f'items: {items}')
            for sub_dir in items:
                if os.path.isdir(os.path.join(compress_dir, sub_dir)):
                    temp_dir = os.path.join(temp_dir, sub_dir)

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

        compile_path = os.path.join(code_dir, '*')
        output_file = os.path.join('/tmp', 'binary_run_file')


        if not compress_dir and not code_dir:
            raise Exception(f'get code from {self.s3_bucket}:{self.s3_key} failed')

        entry_point = os.path.join(code_dir, self.entry_point_file)
        import datetime
        starttime = datetime.datetime.now()
        command_compile_binary_package = f"python -m nuitka --nofollow-imports {entry_point}" \
                                         f" --include-plugin-files={compile_path} " \
                                         f"--output-filename={output_file} --output-dir=/tmp"

        try:

            ret = subprocess.run(command_compile_binary_package, shell=True, capture_output=False, encoding='utf-8', timeout=50, check=True)
            endtime = datetime.datetime.now()
            print(f'command cost : {endtime - starttime}')

            validate_status(ret.returncode, command_compile_binary_package)
            logger.info(f'execute command {command_compile_binary_package} finish')
            logger.info(ret)
        except Exception as e:
            logger.info(e)

        with open(output_file, 'rb') as f:
            binary_key = os.path.join(self.s3_key.split('/')[0], 'binary_run_file')

            s3_client.upload_fileobj(f, self.s3_bucket, binary_key)

        ret = subprocess.run(f"rm -rf {compress_dir}", shell=True, capture_output=True, encoding='utf-8')
        logger.info(f'remove_dir : {compress_dir}')



def handler(event, context):
    logger.info(f'receive event: {event}, type: {type(event)}')
    if 's3_path' not in event or 'entry_point' not in event:
        raise ValueError(f'invalid format {event}')
    s3_path = event['s3_path']
    entry_point = event['entry_point']
    build = CodeBuilder(s3_path, entry_point)
    build.build()


