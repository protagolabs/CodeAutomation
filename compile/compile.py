import os
import uuid
import json

import boto3
import subprocess

import logging
from compile.tool import uncompress_code, lambda_invoke
from dynamodb.job_event import job_event_dao, EventLevel
try:
    from Const import JobStatus
except ModuleNotFoundError:
    from boto3_layer.python.Const import JobStatus

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

class CodeBuilder:
    def __init__(self, job_id, s3_path, entry_point) -> None:
        self.job_id = job_id
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

            logger.info(f'download {self.s3_bucket}, {self.s3_key}')
            s3_client.download_file( self.s3_bucket, self.s3_key, write_obj)


            temp_dir = "/tmp/" + str(uuid.uuid4())
            os.makedirs(temp_dir, exist_ok=True)
            uncompress_code(write_obj, temp_dir)
            logger.info(f'uncompress to {temp_dir}')
            compress_dir = temp_dir

            items = os.listdir(temp_dir)
            logger.info(f'items: {items}')
            for sub_dir in items:
                if sub_dir == '__MACOSX':
                    continue
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
        if not compress_dir or not code_dir:
            raise Exception(f'download code from {self.s3_bucket}:{self.s3_key} failed')

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
    field_list = ['s3_path', 'entry_point', 'job_id']

    for field in field_list:
        if field not in json_body:
            raise ValueError(f'invalid format {event}')
    job_id = json_body['job_id']
    s3_path = json_body['s3_path']
    entry_point = json_body['entry_point']
    try:
        build = CodeBuilder(job_id, s3_path, entry_point)
        build.build()
    except Exception:
        event_msg = f"compile by event {json_body} failed"
        job_event_dao.quick_insert(job_id, JobStatus.FAILED, EventLevel.ERROR, event_msg)


