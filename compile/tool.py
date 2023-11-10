import os
import json
import uuid

import boto3
import zipfile
import tarfile
import tempfile
from multipledispatch import dispatch


region = os.getenv("REGION", "us-west-2")
s3_client = boto3.client('s3', region_name = region)

region = os.getenv("REGION", "us-west-2")

lambda_invoker = boto3.client('lambda', region_name = region)

def _uncompress_zip(file_path, dest):
    zFile = zipfile.ZipFile(file_path, "r")
    for fileM in zFile.namelist():
        zFile.extract(fileM, dest)
    zFile.close()


def _compress_tar(file_path, dest):
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(file_path, arcname=os.path.basename(file_path))


def _uncompress_tar(file_path, dest):
    print(f'file_path: {file_path} dest: {dest}')
    tar = tarfile.open(file_path, "r:*")

    code_files = tar.getnames()
    for code_file in code_files:
        tar.extract(code_file, dest)

def get_transformed_entry_file_name(origin_name):
    #file_name = origin_name.split('/')[0]
    print(f'origin_name: {origin_name}')

    # python can not import module that starts with number.
    file_name = "main_" + str(uuid.uuid4()).replace('-', '')
    suffix = origin_name.split('/')[1].split('.')[1]
    final_file_name = '.'.join([file_name, suffix])
    return final_file_name

def uncompress_code(suffix_name, file_path, dest):
    final_file_name = None
    if suffix_name.endswith(".zip"):
        _uncompress_zip(file_path, dest)

    elif suffix_name.endswith(".tar") or suffix_name.endswith(".tar.gz"):
        _uncompress_tar(file_path, dest)
    else:
        final_file_name = get_transformed_entry_file_name(suffix_name)
        dir_name = os.path.dirname(file_path)
        src_file_name = os.listdir(dir_name)[0]
        import shutil
        shutil.move(os.path.join(dir_name, src_file_name), os.path.join(dest, final_file_name))
    return final_file_name


def lambda_auth():
    return {"uid": "netmind"}

"""
invode another lambda function
"""

@dispatch(str, dict)
def lambda_invoke(function, payload, as_admin=False, async_call=False):
    if as_admin:
        payload = dict(payload, **lambda_auth())
    return lambda_invoke_inner(function, json.dumps(payload), async_call=async_call)

@dispatch(str, str)
def lambda_invoke_inner(function, payload, async_call=False):
    invoke_type = "Event" if async_call else "RequestResponse"
    response = lambda_invoker.invoke(
        FunctionName=function, InvocationType=invoke_type, Payload=payload
    )
    if "Payload" in response and not async_call:
        return json.load(response["Payload"])
    return None


