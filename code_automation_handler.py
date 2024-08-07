import ast
import glob
import json
import os
import re
import shutil
import tarfile
import tempfile
import uuid
import zipfile
from uuid import uuid4

try:
    from AwsServices import aws
    from beans.Ret import Ret
    from Const import (
        AwsS3,
        HttpCode,
    )
    from errors.CustomExceptions import (
        AwsServiceOperationException,
        ResourceNotFoundException,
        StatusCheckFailedException,
    )
    from Logging import get_logger
    from utils.Tools import dir_to_json, todict, uncompress_code
except ModuleNotFoundError:
    from boto3_layer.python.AwsServices import aws
    from boto3_layer.python.Const import (
        AwsS3,
        HttpCode,
    )
    from boto3_layer.python.Logging import get_logger
    from webkit_layer.python.beans.Ret import Ret
    from webkit_layer.python.errors.CustomExceptions import (
        AwsServiceOperationException,
        ResourceNotFoundException,
        StatusCheckFailedException,
    )
    from webkit_layer.python.utils.Tools import dir_to_json, todict, uncompress_code


from auto_complete.hivemind_mlm_handler import (
    HivemindCallbackMonitorHandler,
    hm_mlm_callback_code_injection_list,
)
from auto_complete.hivemind_resnet_handler import (
    HivemindResnetOptimizerHandler,
    HivemindResnetRunTrainerHandler,
    HivemindResnetTrainerHandler,
    hm_resnet_optimizer_injection_list,
    hm_resnet_run_hm_resnet_trainer_injection_list,
    hm_resnet_trainer_injection_list,
)
from auto_complete.tensorflow_custom import (
    TensorflowCustomHandler,
    init_custom_tf_injection_list,
    tensorflow_custom_visited_table,
    tf_custom_code_injection_list,
)
from auto_complete.tensorflow_trainer import (
    TensorflowTrainerHandler,
    init_callback_tf_injection_list,
    tensorflow_trainer_visited_table,
    tf_trainer_code_injection_list,
)
from auto_complete.tool import (
    CodeNotCompliantException,
    CodeTemplateNotLegalException,
    InjectionOperation,
)
from auto_complete.torch_custom_with_eval import (
    TorchCustomWithEvalTrainDistHandler,
    TorchCustomWithEvalTrainerHandler,
    init_custom_with_eval_injection_list,
    pytorch_resnet_custom_visited_table,
    torch_cus_eval_dist_code_injection_list,
    torch_cus_eval_trainer_code_injection_list,
)
from auto_complete.torch_custom_without_eval import (
    TorchCustomWithOutEvalTrainDistHandler,
    TorchCustomWithOutEvalTrainerHandler,
    init_custom_without_eval_injection_list,
    pytorch_mlm_custom_visited_table,
    torch_no_eval_dist_code_injection_list,
    torch_no_eval_trainer_code_injection_list,
)
from auto_complete.torch_trainer import (
    TorchTrainerHandler,
    init_transformers_injection_list,
    pytorch_trainer_visited_table,
    torch_trainer_dist_code_injection_list,
    torch_trainer_trainer_code_injection_list,
)
from automation_common.bean.domain.CodeStructureDo import CodeStructureDo
from automation_common.dao.CodeStructureDao import code_structure_dao
from automation_common.JobConst import (
    FileLoc,
    Regex,
)
from automation_common.Messages import msg
from common.security import contain_bad_os_exec, contain_miner_code
from template_platform import (
    CodePlatform,
)

logger = get_logger(__name__)


class CodeAutomationHandler:
    def payload_check(self, event):
        if "payload" not in event:
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("payload")
            )

    """
    Check if the request has jobid
    """

    def resource_check(self, event):
        self.payload_check(event)

        if "jobid" not in event["payload"]:
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("jobid")
            )

    def insert_code(self, code_platform, temp_dir):

        update_file_dict = {
            CodePlatform.TENSORFLOW_CUSTOM_TRAINER: (
                ["train_netmind.py"],
                [tf_custom_code_injection_list],
                TensorflowCustomHandler,
                tensorflow_custom_visited_table,
                init_custom_tf_injection_list,
            ),
            CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER: (
                ["train_netmind.py"],
                [tf_trainer_code_injection_list],
                TensorflowTrainerHandler,
                tensorflow_trainer_visited_table,
                init_callback_tf_injection_list,
            ),
            CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL: (
                ["train_dist.py", "trainer.py"],
                [
                    torch_cus_eval_dist_code_injection_list,
                    torch_cus_eval_trainer_code_injection_list,
                ],
                [
                    TorchCustomWithEvalTrainDistHandler,
                    TorchCustomWithEvalTrainerHandler,
                ],
                pytorch_resnet_custom_visited_table,
                init_custom_with_eval_injection_list,
            ),
            CodePlatform.PYTORCH_CUSTOM_TRAINER: (
                ["train_dist.py", "trainer.py"],
                [
                    torch_no_eval_dist_code_injection_list,
                    torch_no_eval_trainer_code_injection_list,
                ],
                [
                    TorchCustomWithOutEvalTrainDistHandler,
                    TorchCustomWithOutEvalTrainerHandler,
                ],
                pytorch_mlm_custom_visited_table,
                init_custom_without_eval_injection_list,
            ),
            CodePlatform.PYTORCH_TRANSFORMERS_TRAINER: (
                ["train_dist.py", "trainer.py"],
                [
                    torch_trainer_dist_code_injection_list,
                    torch_trainer_trainer_code_injection_list,
                ],
                TorchTrainerHandler,
                pytorch_trainer_visited_table,
                init_transformers_injection_list,
            ),
            CodePlatform.HIVEMIND_CUSTOM_TRAINER: (
                ["optimizer.py", "run_trainer.py", "trainer.py"],
                [
                    hm_resnet_optimizer_injection_list,
                    hm_resnet_run_hm_resnet_trainer_injection_list,
                    hm_resnet_trainer_injection_list,
                ],
                [
                    HivemindResnetOptimizerHandler,
                    HivemindResnetRunTrainerHandler,
                    HivemindResnetTrainerHandler,
                ],
            ),
            CodePlatform.HIVEMIND_TRANSFORMERS_TRAINER: (
                [
                    "callback.py",
                ],
                [hm_mlm_callback_code_injection_list],
                [HivemindCallbackMonitorHandler],
            ),
        }

        if code_platform not in update_file_dict.keys():
            logger.error(f"error code platform : {code_platform}, check {temp_dir}")
            raise CodeNotCompliantException(f"error code platform : {code_platform}")

        missing_feature_point_list = []

        visited_table = update_file_dict[code_platform][3]
        # reset visited table
        for value in visited_table.values():
            value[0] = False

        # for meta_list in update_file_dict[code_platform][1]:
        #    meta_list
        update_file_dict[code_platform][4]()
        delay_insertion_table = {}
        for index, train_file in enumerate(update_file_dict[code_platform][0]):
            target_file = temp_dir + train_file
            if not os.path.exists(target_file):
                logger.warning(f"{target_file} does not exists")
                raise CodeNotCompliantException(f"{target_file} does not exists")
            logger.info(f"reading {target_file}")

            ast_root = ast.parse(open(target_file).read())

            print(f"meta list : {update_file_dict[code_platform][1][index]}")
            if isinstance(update_file_dict[code_platform][2], list):
                update_file_dict[code_platform][2][index]().visit(ast_root)
            else:
                update_file_dict[code_platform][2]().visit(ast_root)

            logger.info(f"visit file  {target_file} success")
            ast.fix_missing_locations(ast_root)

            sorted_code_list = sorted(
                update_file_dict[code_platform][1][index],
                key=lambda x: (x.insert_line_no, x.operation),
                reverse=True,
            )
            with open(target_file, "r") as f:
                lines = f.readlines()
                for elem in sorted_code_list:
                    logger.info(
                        f"insert {target_file}, line : {elem.insert_line_no}, content : {elem.insert_expr} "
                        f"offset : {elem.col_offset}"
                    )
                    if elem.operation == InjectionOperation.ADD:
                        # if insert in lastest line, must confirm there exists \n character after last line
                        if elem.insert_expr[-1] != "\n":
                            # print(f'elem.insert_line_no : {elem.insert_line_no}, elem.insert_expr: {elem.insert_expr}')
                            # lines.insert(elem.insert_line_no, "\n")
                            lines[elem.insert_line_no - 1] += "\n"
                        lines.insert(
                            elem.insert_line_no,
                            " " * elem.col_offset + elem.insert_expr + "\n",
                        )
                    elif elem.operation == InjectionOperation.DELETE:
                        del lines[elem.insert_line_no - 1]
                s = "".join(lines)
            delay_insertion_table[target_file] = s

        for k, v in delay_insertion_table.items():
            with open(k, "w") as f:
                f.write(v)

        logger.info(f"visited_table.values() : {visited_table.values()}")
        for item in visited_table.values():
            if not item[0]:
                if item[1] not in missing_feature_point_list:
                    missing_feature_point_list.append(item[1])
        if len(missing_feature_point_list) > 0:
            str_missing_feature_point = "\n".join(missing_feature_point_list)

            logger.error(f"error str_missing_feature_point:{str_missing_feature_point}")
            raise CodeTemplateNotLegalException(
                f"missing \n {str_missing_feature_point}"
            )

        return

    def handle_compressed_package(self, destination_dir):
        max_uncompress_time = 5
        suffix_pattern = [".zip", ".tar.gz", ".tar"]
        compress_record_table = {}
        while max_uncompress_time > 0:
            compress_record_table[str(max_uncompress_time)] = {}
            for pattern in suffix_pattern:
                glob_list = glob.glob(
                    f"{destination_dir}/**/*{pattern}", recursive=True
                )
                if len(glob_list) > 0:
                    compress_record_table[str(max_uncompress_time)][pattern] = True
                else:
                    compress_record_table[str(max_uncompress_time)][pattern] = False
                logger.info(
                    f"max_uncompress_time: {max_uncompress_time}, glob_list: {glob_list},  pattern:{pattern}, destination_dir:{destination_dir}"
                )
                for matched_file in glob_list:
                    matched_file_dir_name = os.path.dirname(matched_file)
                    uncompress_code(matched_file, matched_file_dir_name)
                    logger.debug(
                        f"uncompress {matched_file} to {matched_file_dir_name}"
                    )
                    os.system(f"rm {matched_file}")
            # whther skip this loop
            vals = compress_record_table[str(max_uncompress_time)].values()
            if True not in vals:
                break

            max_uncompress_time -= 1

    def __handle_progress_command(self, line):
        progress_command = ["tar", "zip", "unzip", "wget"]
        null_pattern = "1>/dev/null 2>&1"
        for command in progress_command:
            if line.find(command) != -1:
                return f"os.system(f'{line.strip()} {null_pattern}')\n"
        return f"os.system(f'{line.strip()} ')\n"

    def remove_prefix(self, line):
        exclamation_point = "!"
        percent_sign_with_cd = "%cd"
        percent_sign = "%"
        double_percent_sign = "%%"
        legal_percent_sign_list = [
            "%pwd",
            "%ls",
            "%cp",
            "%mv",
            "%mkdir",
            "%rm",
            "%rmdir",
            "%cat",
            "%pip",
            "%conda",
            "%env",
            "%setenv",
        ]

        leading_spaces = len(line) - len(line.lstrip())
        without_leading_spaces_line = line.lstrip()

        special_pattern = False

        if without_leading_spaces_line.startswith(exclamation_point):
            line = line.replace(exclamation_point, "").rstrip()

            line = self.__handle_progress_command(line)
            special_pattern = True

        elif without_leading_spaces_line.startswith(percent_sign):
            line = line.rstrip()
            if without_leading_spaces_line.startswith(double_percent_sign):
                line = f"#{line}\n"
            elif without_leading_spaces_line.startswith(percent_sign_with_cd):
                line = line.replace(percent_sign_with_cd, "")
                line = f"os.chdir(f'{line.strip()}')\n"
            else:
                word_list = without_leading_spaces_line.split("\n")[0].split(" ")

                first_word = word_list[0]
                if first_word in legal_percent_sign_list:
                    line = line.replace(percent_sign, "")
                    line = f"os.system(f'{line.strip()} ')\n"
                else:
                    line = "pass\n"
            special_pattern = True
        if special_pattern:
            line = " " * leading_spaces + line
        return line

    def handle_security(self, temp_dir):
        for file in glob.glob(f"{temp_dir}/**/*", recursive=True):
            code = open(file)
            content = code.read()
            if contain_miner_code(content):
                raise Exception(f"contain miner code in {file}, please check")
            unsafe, reason = contain_bad_os_exec(content)
            if unsafe:
                raise Exception(reason)

    def handle_ipynb(self, temp_dir):
        for file in glob.glob(f"{temp_dir}/**/*.ipynb", recursive=True):

            code = json.load(open(file))
            dirname = os.path.dirname(file)
            fine_name = os.path.basename(file)
            file_name = fine_name.split(".")[0] + ".py"
            target_file = os.path.join(dirname, file_name)

            with open(target_file, "w+") as py_file:
                py_file.write("import os\n")
                for cell in code["cells"]:
                    if cell["cell_type"] == "code":
                        for line in cell["source"]:
                            line = self.remove_prefix(line)
                            py_file.write(line)
                        py_file.write("\n")

            os.system(f"rm {file}")

    """
    def check(self, event):
        self.payload_check(event)
        if not event["payload"].get("code_file"):
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("payload.code_file")
            )

        result = re.search(Regex.S3_CODE_FILE_URI, event["payload"]["code_file"])
        if result is None:
            raise ResourceNotFoundException(msg.S3_CODE_URI_ERROR)

        platform_checker = PlatformChecker()
        s3_key = result.group(1)

        temp_dir = "/tmp/" + str(uuid4())
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"downloading {AwsS3.S3_JOB_MODEL_CODE_BUCKET} by key : {s3_key}")
        tf = aws.s3_download_to_tempfile(AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key)

        uncompress_code(tf.name, temp_dir)


        output = [
            directory
            for directory in os.listdir(temp_dir)
            if os.path.isdir(os.path.join(temp_dir, directory))
        ]
        if len(output) >= 2:
            if "__MACOSX" in output:
                del output[output.index("__MACOSX")]

        temp_dir += '/'
        file_list = os.listdir(temp_dir)
        file_list = set(filter(lambda x: x.endswith(".py"), file_list))
        if len(file_list) > 0:
            #py file exists in code pacakge root dir
            origin_dir = os.path.dirname(temp_dir) + '/'
        else:
            file_dir = output[0] if len(output) == 1 else ""
            origin_dir = temp_dir
            temp_dir = temp_dir + file_dir + "/"

        self.handle_ipynb(temp_dir)
        code_platform = platform_checker.check_from_dir(temp_dir)

        # save directory structure
        code_file_json = dir_to_json(temp_dir)
        try:
            code_structure_do = code_structure_dao.get_by_s3_key(s3_key)
            code_structure_dao.update_by_id(
                code_structure_do.id, structure=json.dumps(code_file_json)
            )
        except ResourceNotFoundException:
            logger.warn("Related code object not found, create it.")
            code_structure_do = CodeStructureDo(
                str(uuid.uuid4()), s3_key, json.dumps(code_file_json), FileLoc.S3
            )
            code_structure_dao.insert_one(code_structure_do.__dict__)

        def _compress_tar(file_path):
            if s3_key.endswith(".tar") or s3_key.endswith(".tar.gz"):
                with tempfile.TemporaryFile(suffix=".tar.gz") as f:
                    with tarfile.open(fileobj=f, mode="w:gz", compresslevel=5) as tar:
                        arcname = os.path.basename(file_path)
                        print(f"add {file_path} , {arcname}")
                        tar.add(file_path, arcname=os.path.basename(file_path))
                    f.flush()
                    f.seek(0)
                    logger.info(
                        f"s3_put_by_tmp by {AwsS3.S3_JOB_MODEL_CODE_BUCKET}, {s3_key}"
                    )
                    aws.s3_put_by_tmp(f, AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key)
            elif s3_key.endswith(".zip"):
                with tempfile.TemporaryFile(suffix=".zip") as f:
                    with zipfile.ZipFile(f, "w") as zip_file:
                        dir_name = ""
                        for root, dir, files in os.walk(file_path):
                            if len(dir) > 0:
                                dir_name = dir[0]
                            for file in files:
                                zip_file.write(
                                    os.path.join(root, file),
                                    arcname=os.path.join(dir_name, file),
                                )
                    f.flush()
                    f.seek(0)
                    aws.s3_put_by_tmp(f, AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key)

        # upload origin package with another
        s3_key_list = s3_key.split('/')
        filename_list = s3_key_list[1].split('.')
        filename_list[0] = filename_list[0] + '_origin_package'
        origin_package_name = '.'.join(filename_list)
        s3_origin_package_key = '/'.join([s3_key_list[0], origin_package_name])

        with open(tf.name, 'rb') as f:
            logger.info(
                f"s3_put_by_tmp by {AwsS3.S3_JOB_MODEL_CODE_BUCKET}, {s3_origin_package_key}"
            )
            aws.s3_put_by_tmp(f, AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_origin_package_key)

        try:

            self.insert_code(code_platform, temp_dir)
            _compress_tar(origin_dir)
        except DuplicateInjectionError:
            logger.warning("duplicate injection is forbidded")

        except (CodeNotCompliantException, Exception) as e:
            logger.error("insert code failed")
            logger.exception(e)
            raise e

        code_checker = CodeChecker()
        self.validate_netmind_interface(code_checker, code_platform, temp_dir)
        shutil.rmtree(temp_dir)
        return {
            "warn": code_checker.warn,
            "error": code_checker.error,
            "structure": code_structure_do.structure,
        }
    """

    def check(self, event):
        self.payload_check(event)
        if not event["payload"].get("code_file"):
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("payload.code_file")
            )

        result = re.search(Regex.S3_CODE_FILE_URI, event["payload"]["code_file"])
        if result is None:
            raise ResourceNotFoundException(msg.S3_CODE_URI_ERROR)

        s3_key = result.group(1)

        temp_dir = "/tmp/" + str(uuid4())
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"downloading {AwsS3.S3_JOB_MODEL_CODE_BUCKET} by key : {s3_key}")

        tf = None
        if (
            s3_key.endswith(".tar")
            or s3_key.endswith(".tar.gz")
            or s3_key.endswith(".zip")
        ):
            tf = aws.s3_download_to_tempfile(AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key)
            uncompress_code(tf.name, temp_dir)

            self.handle_compressed_package(temp_dir)

        elif s3_key.endswith("ipynb") or s3_key.endswith("py"):
            target_file_name = s3_key.split("/")[1]
            with open(os.path.join(temp_dir, target_file_name), "wb") as tf:
                aws.s3_download_file(AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key, tf)

        output = [
            directory
            for directory in os.listdir(temp_dir)
            if os.path.isdir(os.path.join(temp_dir, directory))
        ]
        if len(output) >= 2:
            if "__MACOSX" in output:
                del output[output.index("__MACOSX")]

        temp_dir += "/"
        file_list = os.listdir(temp_dir)
        file_list = set(filter(lambda x: x.endswith(".py"), file_list))
        ipynb_list = set(filter(lambda x: x.endswith(".ipynb"), file_list))
        origin_dir = temp_dir
        if len(ipynb_list) == 0 and len(file_list) == 0:
            # py file exists in code pacakge root dir
            file_dir = output[0] if len(output) == 1 else None
            if file_dir:
                temp_dir = os.path.join(temp_dir, file_dir)

        # save directory structure
        code_file_json = dir_to_json(temp_dir)
        try:
            code_structure_do = code_structure_dao.get_by_s3_key(s3_key)
            code_structure_dao.update_by_id(
                code_structure_do.id, structure=json.dumps(code_file_json)
            )
        except ResourceNotFoundException:
            logger.warn("Related code object not found, create it.")
            code_structure_do = CodeStructureDo(
                str(uuid.uuid4()), s3_key, json.dumps(code_file_json), FileLoc.S3
            )
            code_structure_dao.insert_one(code_structure_do.__dict__)
        self.handle_ipynb(temp_dir)
        self.handle_security(temp_dir)

        def _compress_tar(dir_path):
            if s3_key.endswith(".tar") or s3_key.endswith(".tar.gz"):
                with tempfile.TemporaryFile(suffix=".tar.gz") as f:
                    with tarfile.open(fileobj=f, mode="w:gz", compresslevel=5) as tar:
                        arcname = os.path.basename(dir_path)
                        logger.info(f"add {dir_path} , {arcname}")
                        tar.add(dir_path, arcname=os.path.basename(dir_path))
                    f.flush()
                    f.seek(0)
                    logger.info(
                        f"s3_put_by_tmp by {AwsS3.S3_JOB_MODEL_CODE_BUCKET}, {s3_key}"
                    )
                    aws.s3_put_by_tmp(f, AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key)
            elif s3_key.endswith(".zip"):
                with tempfile.TemporaryFile(suffix=".zip") as f:
                    with zipfile.ZipFile(f, "w") as zip_file:
                        for root, dir, files in os.walk(dir_path):

                            if len(files) > 0:
                                print(f"root: {root}, dir_path: {dir_path}")
                                arc_dir_name = root.lstrip(dir_path)
                            for file in files:
                                write_file_name = os.path.join(root, file)
                                arc_name = os.path.join(arc_dir_name, file)
                                print(
                                    f"write write_file_name:{write_file_name}, arcname:{arc_name}"
                                )
                                zip_file.write(
                                    write_file_name,
                                    arcname=arc_name,
                                )

                    f.flush()
                    f.seek(0)
                    aws.s3_put_by_tmp(f, AwsS3.S3_JOB_MODEL_CODE_BUCKET, s3_key)
            elif s3_key.endswith(".ipynb"):
                py_key = s3_key.split(".")[0] + ".py"
                file_path = os.path.join(dir_path, py_key.split("/")[1])
                logger.info(f"push {AwsS3.S3_JOB_MODEL_CODE_BUCKET}:{py_key}")
                with open(file_path, "rb") as f:
                    aws.s3_put_by_tmp(f, AwsS3.S3_JOB_MODEL_CODE_BUCKET, py_key)
                os.system(f"rm {file_path}")

        # upload origin package with another
        s3_key_list = s3_key.split("/")
        filename_list = s3_key_list[1].split(".")
        filename_list[0] = filename_list[0] + "_origin_package"

        _compress_tar(origin_dir)

        logger.info(
            f"package already upload to {AwsS3.S3_JOB_MODEL_CODE_BUCKET} {s3_key}"
        )

        shutil.rmtree(temp_dir)
        return {
            "warn": [],
            "error": [],
            "structure": code_structure_do.structure,
        }

    def validate_netmind_interface(self, code_checker, code_platform, code_path):

        code_checker_dict = {
            CodePlatform.PYTORCH_CUSTOM_TRAINER: code_checker.pytorch_custom_trainer_do_check,
            CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL: code_checker.pytorch_custom_witheval_trainer_do_check,
            CodePlatform.PYTORCH_TRANSFORMERS_TRAINER: code_checker.pytorch_transformers_trainer_do_check,
            CodePlatform.TENSORFLOW_CUSTOM_TRAINER: code_checker.tensorflow_custom_trainer_do_check,
            CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER: code_checker.tensorflow_callback_trainer_do_check,
            CodePlatform.HIVEMIND_CUSTOM_TRAINER: code_checker.hivemind_custom_trainer_do_check,
            CodePlatform.HIVEMIND_TRANSFORMERS_TRAINER: code_checker.hivemind_transformers_trainer_do_check,
        }

        if code_platform not in code_checker_dict.keys():
            raise ValueError(f"code_platform : {code_platform} not recognized")
        logger.info(f"code_platform : {code_platform}")
        code_checker_dict[code_platform](code_path, code_platform)

    def get_code_structure(self, event):
        self.payload_check(event)

        if not event["payload"].get("s3_url"):
            raise ResourceNotFoundException(
                msg.RESOURCE_NOT_FOUND_MESSAGE_TEMPLATE.format("s3_url")
            )

        result = re.search(Regex.S3_CODE_FILE_URI, event["payload"]["s3_url"])
        if result is None:
            raise ResourceNotFoundException(msg.S3_CODE_URI_ERROR)

        return code_structure_dao.get_by_s3_key(result.group(1))

    def action(self, action):
        actions = {"check": self.check, "get_code_structure": self.get_code_structure}
        return actions.get(action)

    """
    Handle api request
    """

    def api_gateway(self, event, context) -> Ret:
        try:
            logger.debug(event)

            return Ret.ok(
                data=self.action(event["action"])(event), code=HttpCode.HTTP_OK
            )
        except (
            ResourceNotFoundException,
            AwsServiceOperationException,
            StatusCheckFailedException,
            Exception,
        ) as e:
            logger.exception(e)
            return Ret.fail(
                msg=(e.msg if hasattr(e, "msg") else str(e)),
                code=HttpCode.HTTP_INTERNAL_SERVER_ERROR,
            )


"""
handle
"""

code_automation_handler = CodeAutomationHandler()


def handle(event, context):
    return todict(code_automation_handler.api_gateway(event, context))


if __name__ == "__main__":
    service = CodeAutomationHandler()

    # payload = {
    #     "action": "check",
    #     "payload": {
    #         "code_file": "https://protagolabs-netmind-job-model-code-prod.s3.amazonaws.com/41436775-6787-41b4-9e00-b80b840b8aaf/sovits4_colab.ipynb"
    #     },
    # }

    # ret = service.api_gateway(payload, None)
    service.handle_ipynb("/Users/yizhou/code/temp/mine")
    service.handle_security("/Users/yizhou/code/temp/mine")
