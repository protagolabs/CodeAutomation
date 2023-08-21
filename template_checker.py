import ast
import os
import shutil
from typing import Tuple
from uuid import uuid4

from ast_checker import AstChecker

try:
    from AwsServices import aws
    from Const import AwsS3
    from utils.Tools import uncompress_code
except ModuleNotFoundError:
    from boto3_layer.python.AwsServices import aws
    from boto3_layer.python.Const import AwsS3
    from webkit_layer.python.utils.Tools import uncompress_code
from template_platform import CodePlatform

platform_check_file_dict = {
    CodePlatform.TENSORFLOW_CUSTOM_TRAINER: ["train_netmind.py"],
    CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER: ["train_netmind.py"],
    CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL: ["train_dist.py", "trainer.py"],
    CodePlatform.PYTORCH_CUSTOM_TRAINER: ["train_dist.py", "trainer.py"],
    CodePlatform.PYTORCH_TRANSFORMERS_TRAINER: ["train_dist.py", "trainer.py"],
    CodePlatform.HIVEMIND_CUSTOM_TRAINER: [
        "optimizer.py",
        "run_trainer.py",
        "trainer.py",
    ],
    CodePlatform.HIVEMIND_TRANSFORMERS_TRAINER: ["callback.py"],
}


class Level:
    WARN = ("warn",)
    ERROR = "error"


class CheckPoint:
    def __init__(self, ast_type, level, original_full_path, reason=None) -> None:
        self.ast_type = ast_type
        self.level = level
        self.original_full_path = original_full_path
        self.imported_name = []
        self.exist = False
        self.reason = reason


class CodeChecker(AstChecker):
    def __init__(self) -> None:
        self.warn = []
        self.error = []

    def clear(self):
        self.warn.clear()
        self.error.clear()

    def ast_nodes_from_s3(self, model_code_s3_key):
        temp_dir = "/tmp/" + str(uuid4())
        os.makedirs(temp_dir, exist_ok=True)
        tf = aws.s3_download_to_tempfile(
            AwsS3.S3_JOB_MODEL_CODE_BUCKET, model_code_s3_key
        )
        uncompress_code(model_code_s3_key, tf.name, temp_dir)
        ast_nodes = self.ast_nodes_from_dir(temp_dir)
        shutil.rmtree(temp_dir)
        return ast_nodes

    def ast_nodes_from_dir(self, temp_dir, platform):
        file_list = os.listdir(temp_dir)
        ast_nodes = []
        for template_file in platform_check_file_dict[platform]:
            if template_file in file_list:
                with open(os.path.join(temp_dir, template_file), "r") as f:
                    try:
                        ast_nodes.append(ast.parse(f.read()))
                    except Exception as e:
                        self.error.append(
                            "[error] Exceptions occured when parsing file '{}' to ast: {}".format(
                                template_file, e
                            )
                        )
            else:
                self.error.append(
                    "[error] File '{}' not found, we will not be able to verify the use of NetmindPilot in this file".format(
                        template_file
                    )
                )
        return ast_nodes

    """
    error: check "nmp.init()"
    error: add "nmp.finish_training()" to end of file
    """

    def _common_checker(self):
        nmp_init = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.init",
            "ensure NetmindPilot is initialized properly",
        )
        nmp_finish_training = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.finish_training",
            "finish training properly",
        )

        return [nmp_init, nmp_finish_training]


    def _pytorch_custom_evaluate_checker(self):
        nmp_init_eval = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.init_eval_bar",
            "ensure NetmindPilot is initialized properly",
        )
        nmp_evaluate = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.evaluate",
            "finish training properly",
        )

        return [nmp_init_eval, nmp_evaluate]


    def _do_check_by_checker(self, ast_nodes, check_point_list: Tuple[CheckPoint]):
        for ast_node in ast_nodes:
            for check_point in check_point_list:
                check_point.imported_name = self.find_imported_func_name(
                    ast_node, check_point.original_full_path
                )
                print(
                    f"check_point.imported_name : {check_point.imported_name}, original_full_path : {check_point.original_full_path}"
                )
            for node in ast.walk(ast_node):
                for check_point in check_point_list:
                    if not check_point.exist and type(node) in check_point.ast_type:
                        check_point.exist = self._check_attr_or_call_stack(
                            node, check_point.imported_name
                        )

        for check_point in check_point_list:
            if not check_point.exist:
                if check_point.level == Level.WARN:
                    self.warn.append(
                        "[warn] Miss '{}', which is used to {}".format(
                            check_point.original_full_path, check_point.reason
                        )
                    )
                if check_point.level == Level.ERROR:
                    self.error.append(
                        "[error] Miss '{}', which is used to {}".format(
                            check_point.original_full_path, check_point.reason
                        )
                    )

    def _pytorch_custom_trainer_check_point_list(self):
        # nmp_cur_step = CheckPoint([ast.Attribute, ast.Name], Level.WARN, "NetmindMixins.Netmind.nmp.cur_step", "resume properly from last trained checkpoint")
        netmind_distributed_model = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.NetmindDistributedModel",
            "generate training model properly",
        )
        netmind_distributed_optimizer = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.NetmindOptimizer",
            "load model from checkpoint properly",
        )
        nmp_init_train_bar = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.init_train_bar",
            "calculate progress properloy",
        )
        nmp_cur_epoch = CheckPoint(
            [ast.Attribute, ast.Name],
            Level.WARN,
            "NetmindMixins.Netmind.nmp.cur_epoch",
            "resume properly from last trained checkpoint",
        )
        nmp_should_skip_step = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.nmp.should_skip_step",
            "skip completed steps from last trained checkpoint",
        )
        nmp_step = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.step",
            "report progress and upload 'loss' (or other metrics) properly",
        )
        # nmp_save_pretrained_by_step = CheckPoint([ast.Call], Level.WARN, "NetmindMixins.Netmind.nmp.save_pretrained_by_step", "save checkpoint properly")


        check_point_list = [
            nmp_cur_epoch,
            nmp_should_skip_step,
            nmp_step,
            nmp_init_train_bar,
            netmind_distributed_model,
        ]
        check_point_list.extend(self._common_checker())

        return check_point_list

    def _pytorch_transformers_trainer_check_point_list(self):
        custom_trainer_callback = CheckPoint(
            [ast.Attribute, ast.Name],
            Level.WARN,
            "NetmindMixins.Netmind.NetmindTrainerCallback",
            "report custom metrics",
        )
        las_checkpoint_from_netmind = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.nmp.last_checkpoint_from_netmind",
            "resume properly from last trained checkpoint",
        )
        nmp_init = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.init",
            "ensure NetmindPilot is initialized properly",
        )
        check_point_list = [
            custom_trainer_callback,
            las_checkpoint_from_netmind,
            nmp_init,
        ]

        return check_point_list

    def _tensorflow_custom_trainer_check_point_list(self):
        netmind_distributed_model = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.NetmindDistributedModel",
            "generate training model properly",
        )
        # nmp_save_pretrained_by_step = CheckPoint([ast.Call], Level.WARN, "NetmindMixins.Netmind.nmp.save_pretrained_by_step", "save checkpoint properly")
        nmp_init_train_bar = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.init_train_bar",
            "initialize training bar",
        )
        nmp_init_eval_bar = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.init_eval_bar",
            "initialize evaluate bar",
        )

        nmp_should_skip_step = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.nmp.should_skip_step",
            "whther skip this batch",

        )
        nmp_step = CheckPoint(
            [ast.Call],
            Level.ERROR,
            "NetmindMixins.Netmind.nmp.step",
            "invoked in training step, to store checkpoint or report progress",
        )
        nmp_evaluate = CheckPoint(
            [ast.Call],
            Level.WARN,
            "NetmindMixins.Netmind.nmp.evaluate",
            "evaluate training loss and accuracy",
        )

        check_point_list = [
            netmind_distributed_model,
            nmp_init_train_bar,
            nmp_init_eval_bar,
            nmp_should_skip_step,
            nmp_step,
        ]
        check_point_list.extend(self._common_checker())
        return check_point_list

    def _tensorflow_callback_trainer_check_point_list(self):
        custom_trainer_callback = CheckPoint(
            [ast.Attribute, ast.Name],
            Level.WARN,
            "NetmindMixins.Netmind.TensorflowTrainerCallback",
            "report custom metrics",
        )
        # last_checkpoint_from_netmind = CheckPoint([ast.Call], Level.WARN, "NetmindMixins.Netmind.nmp.last_checkpoint_from_netmind", "resume properly from last trained checkpoint")
        check_point_list = [custom_trainer_callback]
        # check_point_list.extend(self._common_checker())
        return check_point_list

    def _hivemind_custom_trainer_check_point_list(self):
        custom_trainer_callback = CheckPoint(
            [ast.Attribute, ast.Name],
            Level.WARN,
            "NetmindMixins.Netmind.htp",
            "report custom metrics",
        )
        # last_checkpoint_from_netmind = CheckPoint([ast.Call], Level.WARN, "NetmindMixins.Netmind.nmp.last_checkpoint_from_netmind", "resume properly from last trained checkpoint")
        check_point_list = [custom_trainer_callback]
        # check_point_list.extend(self._common_checker())
        return check_point_list

    def _hivemind_transformers_trainer_check_point_list(self):
        custom_trainer_callback = CheckPoint(
            [ast.Attribute, ast.Name],
            Level.WARN,
            "NetmindMixins.Netmind.hmp",
            "report custom metrics",
        )
        # last_checkpoint_from_netmind = CheckPoint([ast.Call], Level.WARN, "NetmindMixins.Netmind.nmp.last_checkpoint_from_netmind", "resume properly from last trained checkpoint")
        check_point_list = [custom_trainer_callback]
        # check_point_list.extend(self._common_checker())
        return check_point_list

    """
    check custom trainer
    
    error: check "NetmindDistributedModel(...)"
    warn: "dist.barrier()" after "NetmindDistributedModel"
    warn: if use "optimizer", use "NetmindOptimizer"
    error: if train, init "nmp.init_train_bar"
    error: if evaluate, init "nmp.init_eval_bar"
    error: add "nmp.step" to end of your step code
    warn: use "save_pretrained_by_step" instead of "torch.save"
    """

    def pytorch_custom_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._pytorch_custom_trainer_check_point_list()
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)

    def pytorch_custom_witheval_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._pytorch_custom_trainer_check_point_list()
        check_point_list.extend(self._pytorch_custom_evaluate_checker())
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)

    """
    check transformers trainer
    """

    def pytorch_transformers_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._pytorch_transformers_trainer_check_point_list()
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)

    """
    check tensorflow custom trainer
    """

    def tensorflow_custom_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._tensorflow_custom_trainer_check_point_list()
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)

    """
    check tensorflow callback trainer
    """

    def tensorflow_callback_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._tensorflow_callback_trainer_check_point_list()
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)

    """
    check hivemind custom trainer
    """

    def hivemind_custom_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._hivemind_custom_trainer_check_point_list()
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)

    """
    check hivemind transformers trainer
    """

    def hivemind_transformers_trainer_do_check(self, temp_dir, code_platform):
        check_point_list = self._hivemind_transformers_trainer_check_point_list()
        ast_nodes = self.ast_nodes_from_dir(temp_dir, code_platform)
        self._do_check_by_checker(ast_nodes, check_point_list)
