import pytest

# 调用方式二

@pytest.fixture
def login():
    print("输入账号，密码先登录")

@pytest.fixture
def login2():
    print("please输入账号，密码先登录")


@pytest.mark.usefixtures("login2", "login")
def test_s11():
    print("用例 11：登录之后其它动作 111")