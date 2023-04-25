import pytest
import os
import  uuid
import  shutil
from CodeChecker import CodeChecker
from PlatformChecker import CodePlatform, PlatformChecker
from JobCommonService import jobCommonService
from auto_complete.tool import (
    CodeNotCompliantException,
    DuplicateInjectionError
)

os.environ['MODE'] = "copy_before_write"

@pytest.fixture
def platform_checker(scope='class'):
    return PlatformChecker()

@pytest.fixture
def code_checker(scope='class'):
    return CodeChecker()

def generate_new_dir(directory):
    write_dir = f"/tmp/{str(uuid.uuid4())}/"
    print(f'generate writing directory : {write_dir}')
    shutil.copytree(directory, write_dir)
    return write_dir

class TestAccuracyPrompts():
    def test_do_check_local_tf_image_classification_callback(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/local_tf/image-classification/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:

            assert "CustomTrainerCallback(tf.keras.callbacks.Callback)" in e.args[0]
        shutil.rmtree(directory)

    def test_do_check_local_tf_image_classification_custom(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/local_tf/image-classification-custom/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.TENSORFLOW_CUSTOM_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:

            print("---", e.args[0])
            assert "MultiWorkerMirroredStrategy" in e.args[0]
            assert "for epoch in range" in e.args[0]
            assert  "for ds in tqdm" in e.args[0]
        shutil.rmtree(directory)
    def test_do_check_local_tf_language_callback(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/local_tf/language-modeling/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:

            print("---", e.args[0])
            assert "CustomTrainerCallback(tf.keras.callbacks.Callback)" in e.args[0]
            assert "model.fit" in e.args[0]
        shutil.rmtree(directory)

    def test_do_check_local_torch_language_callback(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/local_torch/mlm_trainer_Huggince/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.PYTORCH_TRANSFORMERS_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:

            print("---", e.args[0])
            assert "def train" in e.args[0]
        shutil.rmtree(directory)

    def test_do_check_local_torch_language_custom(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/local_torch/mlm_trainer_customer/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:
            print("---", e.args[0])
            assert "DistributedSampler" in e.args[0]
            assert "DistributedDataParallel" in e.args[0]
            assert "get_optimizer" in e.args[0]
        shutil.rmtree(directory)


    def test_do_check_local_torch_image_custom(self, platform_checker: PlatformChecker):
        directory = "tests/accuracy_prompts/local_torch/resnet/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:
            assert "__main__" in e.args[0]
            assert "validate" in e.args[0]
        shutil.rmtree(directory)


    #test for netmind mode
    def test_do_check_netmind_tf_image_classification_callback(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/netmind_tf/image-classification/"
        directory = generate_new_dir(directory)
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:
            assert "duplicate injection" in e.args[0]

    def test_do_check_netmind_tf_image_classification_custom(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/netmind_tf/image-classification-custom/"
        try:
            platform = platform_checker.check_from_dir(directory)
            assert platform == CodePlatform.TENSORFLOW_CUSTOM_TRAINER
        except Exception as e:
            assert "missing file" in e.args[0]
            assert "arguments.py" in e.args[0]


    def test_do_check_netmind_tf_language_callback(self, platform_checker: PlatformChecker):

        directory = "tests/accuracy_prompts/netmind_tf/language-modeling/"

        try:
            platform = platform_checker.check_from_dir(directory)
            assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER
            jobCommonService.insert_code(platform, directory)
        except Exception as e:
            assert "duplicate injection" in e.args[0]



    def test_do_check_netmind_torch_language_callback(self, platform_checker: PlatformChecker,
                                                      code_checker: CodeChecker):

        directory = "tests/accuracy_prompts/netmind_torch/mlm_trainer_Huggince/"
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.PYTORCH_TRANSFORMERS_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except DuplicateInjectionError:
            print("duplicate injection is forbidded")

            jobCommonService.validate_netmind_interface(code_checker, platform, directory)
            warn_str = ' '.join(code_checker.warn)
            error_str = ' '.join(code_checker.error)
            assert 'nmp.last_checkpoint_from_netmind' in warn_str



    def test_do_check_netmind_torch_language_custom(self, platform_checker: PlatformChecker,
                                                      code_checker: CodeChecker):

        directory = "tests/accuracy_prompts/netmind_torch/mlm_trainer_customer/"
        platform = platform_checker.check_from_dir(directory)
        assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER

        try:
            jobCommonService.insert_code(platform, directory)
        except DuplicateInjectionError:
            print("duplicate injection is forbidded")

            jobCommonService.validate_netmind_interface(code_checker, platform, directory)
            warn_str = ' '.join(code_checker.warn)
            error_str = ' '.join(code_checker.error)
            assert 'nmp.should_skip_step' in warn_str
            assert 'Netmind.NetmindDistributedModel' in warn_str
            assert 'nmp.init' in error_str


    def test_do_check_netmind_torch_image_custom(self, platform_checker: PlatformChecker):
        directory = "tests/accuracy_prompts/netmind_torch/resnet/"
        try:
            platform = platform_checker.check_from_dir(directory)
            assert platform == CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL
        except Exception as e:
            assert "missing file" in e.args[0]
            assert "optimizer.py" in e.args[0]
            assert "arguments.py" in e.args[0]

if __name__ == '__main__':
    pytest.main()