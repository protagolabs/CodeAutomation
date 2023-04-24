import pytest
import os
from CodeChecker import CodeChecker
from PlatformChecker import CodePlatform, PlatformChecker
from JobCommonService import jobCommonService
from auto_complete.tool import (
    CodeNotCompliantException,
    DuplicateInjectionError
)

os.environ['MODE'] = "copy_before_write"

@pytest.fixture
def platform_checker():
    return PlatformChecker()

@pytest.fixture
def code_checker():
    return CodeChecker()

def test_do_check_local_tf_image_classification_callback(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_tf/image-classification/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:

        assert "CustomTrainerCallback(tf.keras.callbacks.Callback)" in e.args[0]

def test_do_check_local_tf_image_classification_custom(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_tf/image-classification-custom/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.TENSORFLOW_CUSTOM_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:

        print("---", e.args[0])
        assert "MultiWorkerMirroredStrategy" in e.args[0]
        assert "for epoch in range" in e.args[0]
        assert  "for ds in tqdm" in e.args[0]
def test_do_check_local_tf_language_callback(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_tf/language-modeling/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:

        print("---", e.args[0])
        assert "CustomTrainerCallback(tf.keras.callbacks.Callback)" in e.args[0]
        assert "model.fit" in e.args[0]

def test_do_check_local_torch_language_callback(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_torch/mlm_trainer_Huggince/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.PYTORCH_TRANSFORMERS_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:

        print("---", e.args[0])
        assert "def train" in e.args[0]

def test_do_check_local_torch_language_custom(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_torch/mlm_trainer_customer/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:
        print("---", e.args[0])
        assert "DistributedSampler" in e.args[0]
        assert "DistributedDataParallel" in e.args[0]
        assert "get_optimizer" in e.args[0]


def test_do_check_local_torch_image_custom(platform_checker: PlatformChecker):
    directory = "tests/accuracy_prompts/local_torch/resnet/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:
        assert "__main__" in e.args[0]
        assert "validate" in e.args[0]


#test for netmind mode
def test_do_check_netmind_tf_image_classification_callback(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/netmind_tf/image-classification/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:
        assert "duplicate injection" in e.args[0]

def test_do_check_netmind_tf_image_classification_custom(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/netmind_tf/image-classification-custom/"
    try:
        platform = platform_checker.check_from_dir(directory)

    except Exception as e:
        assert "missing file" in e.args[0]
        assert "arguments.py" in e.args[0]


def test_do_check_netmind_tf_language_callback(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/netmind_tf/language-modeling/"

    try:
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER
        jobCommonService.insert_code(platform, directory)
    except Exception as e:
        print("---", e.args[0])
        assert "duplicate injection" in e.args[0]



def test_do_check_netmind_torch_language_callback(platform_checker: PlatformChecker,
                                                  code_checker: CodeChecker):

    directory = "tests/accuracy_prompts/netmind_torch/mlm_trainer_Huggince/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.PYTORCH_TRANSFORMERS_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except DuplicateInjectionError:
        print("duplicate injection is forbidded")

        jobCommonService.validate_netmind_interface(code_checker, platform, directory)

        assert code_checker.warn == []
        assert code_checker.error == []

def test_do_check_netmind_torch_language_custom(platform_checker: PlatformChecker,
                                                  code_checker: CodeChecker):

    directory = "tests/accuracy_prompts/netmind_torch/mlm_trainer_customer/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except DuplicateInjectionError:
        print("duplicate injection is forbidded")
        print(f'path : {os.getcwd()}')

        jobCommonService.validate_netmind_interface(code_checker, platform, directory)
        assert code_checker.warn == []
        assert code_checker.error == []



def test_do_check_netmind_torch_image_custom(platform_checker: PlatformChecker):
    directory = "tests/accuracy_prompts/netmind_torch/resnet/"
    try:
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL
    except Exception as e:
        assert "missing file" in e.args[0]
        assert "optimizer.py" in e.args[0]
        assert "arguments.py" in e.args[0]
