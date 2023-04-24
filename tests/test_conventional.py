import pytest
import os
import uuid
import  shutil
from CodeChecker import CodeChecker
from PlatformChecker import CodePlatform, PlatformChecker
from JobCommonService import jobCommonService
from auto_complete.tool import (
    CodeNotCompliantException,
    DuplicateInjectionError
)

os.environ['MODE'] = "copy_before_write"

@pytest.fixture(scope='class')
def platform_checker():
    print('init platform checker')
    return PlatformChecker()

@pytest.fixture(scope='class')
def code_checker():
    print('init code checker')
    return CodeChecker()


class TestConventional():

    @classmethod
    def local_common(
            cls,
            directory,
            expected_platform,
            platform_checker: PlatformChecker,
            code_checker: CodeChecker):
        platform = platform_checker.check_from_dir(directory)
        assert platform == expected_platform

        # copy file directory before write
        if os.environ['MODE'] == "copy_before_write":
            write_dir = f"/tmp/{str(uuid.uuid4())}/"
            print(f'generate writing directory : {write_dir}')
            shutil.copytree(directory, write_dir)

        jobCommonService.insert_code(platform, write_dir)

        jobCommonService.validate_netmind_interface(code_checker, platform, write_dir)
        invalid_netmind_api_dict = {
            "warn": code_checker.warn,
            "error": code_checker.error,
        }
        print(f'invalid_netmind_api_dict: {invalid_netmind_api_dict}')
        assert code_checker.warn == []
        assert code_checker.error == []
        shutil.rmtree(write_dir)

    def test_do_check_local_tf_image_classification_callback(self,
                                                             platform_checker: PlatformChecker,
                                                             code_checker: CodeChecker):

        directory = "tests/conventional/local_tf/image-classification/"
        TestConventional.local_common(directory, CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER, platform_checker, code_checker)

    def test_do_check_local_tf_image_classification_custom(self,
                                                           platform_checker: PlatformChecker,
                                                           code_checker: CodeChecker):
    
        directory = "tests/conventional/local_tf/image-classification-custom/"
        TestConventional.local_common(directory, CodePlatform.TENSORFLOW_CUSTOM_TRAINER, platform_checker, code_checker)


    def test_do_check_local_tf_language_callback(self,
                                                 platform_checker: PlatformChecker,
                                                 code_checker: CodeChecker):
    
        directory = "tests/conventional/local_tf/language-modeling/"
        TestConventional.local_common(directory, CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER, platform_checker, code_checker)
    

    def test_do_check_local_torch_language_callback(self,
                                                    platform_checker: PlatformChecker,
                                                    code_checker: CodeChecker):
    
        directory = "tests/conventional/local_torch/mlm_trainer_Huggince/"
        TestConventional.local_common(directory, CodePlatform.PYTORCH_TRANSFORMERS_TRAINER, platform_checker, code_checker)
    
    
    def test_do_check_local_torch_language_custom(self,
                                                  platform_checker: PlatformChecker,
                                                  code_checker: CodeChecker):
    
        directory = "tests/conventional/local_torch/mlm_trainer_customer/"
        TestConventional.local_common(directory, CodePlatform.PYTORCH_CUSTOM_TRAINER, platform_checker, code_checker)
    
    
    
    def test_do_check_local_torch_image_custom(self,
                                               platform_checker: PlatformChecker,
                                               code_checker: CodeChecker):
        directory = "tests/conventional/local_torch/resnet/"
        TestConventional.local_common(directory, CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL, platform_checker, code_checker)

    @classmethod
    def netmind_common(
            cls,
            directory,
            expected_platform,
            platform_checker: PlatformChecker,
            code_checker: CodeChecker):

        platform = platform_checker.check_from_dir(directory)
        assert platform == expected_platform

        try:
            jobCommonService.insert_code(platform, directory)
        except Exception as e:
            assert "duplicate injection" in e.args[0]

        jobCommonService.validate_netmind_interface(code_checker, platform, directory)
        assert code_checker.warn == []
        assert code_checker.error == []
    

    
    #test for netmind mode
    def test_do_check_netmind_tf_image_classification_callback(self,
                                                               platform_checker: PlatformChecker,
                                                               code_checker: CodeChecker):
    
        directory = "tests/conventional/netmind_tf/image-classification/"
        TestConventional.netmind_common(directory, CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER, platform_checker, code_checker)
    
    
    
    def test_do_check_netmind_tf_image_classification_custom(self,
                                                             platform_checker: PlatformChecker,
                                                             code_checker: CodeChecker):
    
        directory = "tests/conventional/netmind_tf/image-classification-custom/"
        TestConventional.netmind_common(directory, CodePlatform.TENSORFLOW_CUSTOM_TRAINER, platform_checker, code_checker)
    
    
    
    
    def test_do_check_netmind_tf_language_callback(self,
                                                   platform_checker: PlatformChecker,
                                                   code_checker: CodeChecker):
    
        directory = "tests/conventional/netmind_tf/language-modeling/"
        TestConventional.netmind_common(directory, CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER, platform_checker, code_checker)
    
    
    
    
    def test_do_check_netmind_torch_language_callback(self,
                                                      platform_checker: PlatformChecker,
                                                      code_checker: CodeChecker):
    
        directory = "tests/conventional/netmind_torch/mlm_trainer_Huggince/"
        TestConventional.netmind_common(directory, CodePlatform.PYTORCH_TRANSFORMERS_TRAINER, platform_checker, code_checker)
    
    
    
    def test_do_check_netmind_torch_language_custom(self,
                                                    platform_checker: PlatformChecker,
                                                    code_checker: CodeChecker):
    
        directory = "tests/conventional/netmind_torch/mlm_trainer_customer/"
        TestConventional.netmind_common(directory, CodePlatform.PYTORCH_CUSTOM_TRAINER, platform_checker, code_checker)

    
    
    def test_do_check_netmind_torch_image_custom(self,
                                                 platform_checker: PlatformChecker,
                                                 code_checker: CodeChecker):
        directory = "tests/conventional/netmind_torch/resnet/"
        TestConventional.netmind_common(directory, CodePlatform.PYTORCH_CUSTOM_TRAINER_WITH_EVAL, platform_checker, code_checker)


if __name__ == '__main__':
    pytest.main()
