import ast
import os
import shutil
from uuid import uuid4


from AstChecker import AstChecker

try:
    from AwsServices import aws
    from Const import AwsS3
    from Logging import get_logger
    from utils.Tools import uncompress_code
except ModuleNotFoundError:
    from boto3_layer.python.AwsServices import aws
    from boto3_layer.python.Const import AwsS3
    from boto3_layer.python.Logging import get_logger
    from webkit_layer.python.utils.Tools import uncompress_code

logger = get_logger(__name__)


class CodePlatform:
    PYTORCH_CUSTOM_TRAINER = "pytorch_custom_trainer"
    PYTORCH_CUSTOM_TRAINER_WITH_EVAL = "pytorch_custom_with_eval"
    PYTORCH_TRANSFORMERS_TRAINER = "pytorch_transformers_trainer"

    TENSORFLOW_CUSTOM_TRAINER = "tensorflow_custom_trainer"
    TENSORFLOW_TRANSFORMERS_TRAINER = "tensorflow_transformers_trainer"

    HIVEMIND_CUSTOM_TRAINER = "hivemind_custom_trainer"
    HIVEMIND_TRANSFORMERS_TRAINER = "hivemind_transformers_trainer"


class ModuleReferenceChecker:
    def __init__(self, module) -> None:
        self.module = module
        self.imported_objects = []
        self.imported_objects_referenced = False


class PlatformChecker(AstChecker):
    def __init__(self) -> None:

        self.tf_legal_file_name_set = {
            "arguments.py",
            "train_netmind.py"
        }
        """
        self.tf_platform_validation_file_name_set = {
            "train_netmind.py"
        }
        """
        self.torch_legal_file_name_set = {
            "arguments.py",
            "data.py",
            "model.py",
            "optimizer.py",
            "train_dist.py",
            "trainer.py",
        }
        """
        self.torch_platform_validation_file_name_set = {
            "data.py",
            "optimizer.py",
            "train_dist.py",
            "trainer.py",
        }
        """
        self.legal_file_name_set = {
            "train_netmind.py",
            "train_dist.py",
            "trainer.py",
            "optimizer.py",
        }
        #self.legal_intersection = self.tf_legal_file_name_set & self.torch_legal_file_name_set


    def check_from_s3(self, model_code_s3_key):
        temp_dir = "/tmp/" + str(uuid4())
        os.makedirs(temp_dir, exist_ok=True)
        tf = aws.s3_download_to_tempfile(
            AwsS3.S3_JOB_MODEL_CODE_BUCKET, model_code_s3_key
        )
        uncompress_code(tf.name, temp_dir)
        code_platform = self.check_from_dir(temp_dir)
        shutil.rmtree(temp_dir)
        return code_platform

    def check_from_dir(self, temp_dir):
        pytorch_checker = ModuleReferenceChecker("torch")
        tensorflow_checker = ModuleReferenceChecker("tensorflow")
        transformers_checker = ModuleReferenceChecker("transformers")
        hivemind_checker = ModuleReferenceChecker("hivemind")
        data_collector_for_mlm_checker = ModuleReferenceChecker("data_collector")
        tf_trainer_checker = ModuleReferenceChecker("keras_callback")
        checkers = [pytorch_checker, tensorflow_checker, hivemind_checker]


        file_list = os.listdir(temp_dir)
        #validation for missing or mistake file orgnization

        file_list = set(filter(lambda x: x.endswith(".py"), file_list))
        print(file_list)
        unique_file_name = "train_netmind.py"
        if unique_file_name in file_list:
            different_set = self.tf_legal_file_name_set - file_list
        else:
            different_set = self.torch_legal_file_name_set - file_list

        if len(different_set) > 0:
            raise Exception(f'missing file : {different_set}')

        for file in file_list:
            logger.info(f"parsing file : {file}")
            if file not in self.legal_file_name_set:
                continue

            with open(os.path.join(temp_dir, file), "r") as f:
                try:
                    ast_root_node = ast.parse(f.read())
                except Exception as e:
                    raise Exception(f"reading {file} failed, reason : {repr(e)}")

                transformers_trainer_Trainer = self.find_imported_func_name(
                    ast_root_node, "transformers.trainer.Trainer"
                )
                data_collector_for_mlm_validater = self.find_imported_func_name(
                    ast_root_node, "transformers.DataCollatorForLanguageModeling"
                )
                optimizer_validator = self.find_imported_func_name(
                    ast_root_node,
                    "transformers.optimization.get_linear_schedule_with_warmup",
                )
                tf_keras_callback = self.find_imported_func_name(
                    ast_root_node,
                    "tensorflow.keras.callbacks.Callback",
                )
                tf_netmind_callback = self.find_imported_func_name(
                    ast_root_node,
                    "NetmindMixins.Netmind.TensorflowTrainerCallback",
                )

                # do first iteration to find imported class, function, attributes under such module
                for ast_node in ast.walk(ast_root_node):
                    if isinstance(ast_node, ast.ImportFrom):
                        for checker in checkers:
                            if ast_node.module.startswith(checker.module):
                                for name in ast_node.names:
                                    if name.asname:
                                        checker.imported_objects.append(name.asname)
                                    else:
                                        checker.imported_objects.append(name.name)

                    if isinstance(ast_node, ast.Import):
                        for name in ast_node.names:
                            for checker in checkers:
                                # print(f'name.name  : {name.name }')
                                if name.name == checker.module:
                                    if name.asname:
                                        checker.imported_objects.append(name.asname)
                                    else:
                                        checker.imported_objects.append(name.name)

                # do iteration again to find if imported objects are used
                for ast_node in ast.walk(ast_root_node):
                    if isinstance(ast_node, ast.Name):
                        for checker in checkers:
                            if ast_node.id in checker.imported_objects:
                                checker.imported_objects_referenced = True

                    if transformers_trainer_Trainer:

                        if isinstance(ast_node, ast.Call):
                            if self._check_attr_or_call_stack(
                                ast_node, transformers_trainer_Trainer
                            ):
                                transformers_checker.imported_objects_referenced = True
                        elif isinstance(ast_node, ast.ClassDef):
                            if self._check_inherit(
                                ast_node, transformers_trainer_Trainer
                            ):
                                transformers_checker.imported_objects_referenced = True

                    if data_collector_for_mlm_validater:
                        if isinstance(ast_node, ast.Call):
                            if self._check_attr_or_call_stack(
                                ast_node, data_collector_for_mlm_validater
                            ):
                                data_collector_for_mlm_checker.imported_objects_referenced = (
                                    True
                                )

                    if optimizer_validator:
                        if isinstance(ast_node, ast.Call):
                            if self._check_attr_or_call_stack(
                                ast_node, optimizer_validator
                            ):
                                data_collector_for_mlm_checker.imported_objects_referenced = (
                                    True
                                )
                    if tf_keras_callback:
                        if isinstance(ast_node, ast.ClassDef):
                            if self._check_inherit(
                                ast_node, tf_keras_callback
                            ) or self._check_inherit(
                                ast_node, tf_netmind_callback
                            ):
                                tf_trainer_checker.imported_objects_referenced = True


        # build fiter chain to generate final result, its  boolean list corresponding to status list
        status_list = [
            transformers_checker.imported_objects_referenced,
            pytorch_checker.imported_objects_referenced,
            tensorflow_checker.imported_objects_referenced,
            hivemind_checker.imported_objects_referenced,
            tf_trainer_checker.imported_objects_referenced,
            data_collector_for_mlm_checker.imported_objects_referenced,
        ]

        platform_filter_chain = [
            (CodePlatform.HIVEMIND_CUSTOM_TRAINER, [False, True, False, True, False]),
            (
                CodePlatform.HIVEMIND_TRANSFORMERS_TRAINER,
                [True, True, False, True, False],
            ),
            (
                CodePlatform.PYTORCH_TRANSFORMERS_TRAINER,
                [True, True, False, False, False, True],
            ),
            (
                CodePlatform.PYTORCH_CUSTOM_TRAINER,
                [False, True, False, False, False, True],
            ),
            (
                CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL,
                [False, True, False, False, False, False],
            ),
            (
                CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER,
                [False, False, True, False, True],
            ),
            (
                CodePlatform.TENSORFLOW_CUSTOM_TRAINER,
                [False, False, True, False, False],
            ),
        ]

        logger.info(f"final status list : , {status_list}")


        for filter_item in platform_filter_chain:
            ret_platform = filter_item[0]
            expected_status_list = filter_item[1]
            should_return = True
            for index, expected_status in enumerate(expected_status_list):

                if expected_status != status_list[index]:
                    should_return = False
                    break
            if should_return:
                logger.info(
                    f"return ret_platform: {ret_platform}, {expected_status_list}, {status_list}, {index}"
                )
                logger.info(f"return : {ret_platform}")
                return ret_platform
