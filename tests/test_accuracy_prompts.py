import pytest

from PlatformChecker import CodePlatform, PlatformChecker
from JobCommonService import jobCommonService


@pytest.fixture
def platform_checker():
    return PlatformChecker()


def test_do_check_tf_image_classification_callback(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_tf/image-classification/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.TENSORFLOW_TRANSFORMERS_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:
        import traceback
        traceback.print_exc()
        assert "CustomTrainerCallback(tf.keras.callbacks.Callback)" in e.args[0]

def test_do_check_tf_image_classification_custom(platform_checker: PlatformChecker):

    directory = "tests/accuracy_prompts/local_tf/image-classification-custom/"
    platform = platform_checker.check_from_dir(directory)
    assert platform == CodePlatform.TENSORFLOW_CUSTOM_TRAINER

    try:
        jobCommonService.insert_code(platform, directory)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("---", e.args[0])
        assert "CustomTrainerCallback(tf.keras.callbacks.Callback)" in e.args[0]

