from CodeAutomation import hello

def test_hello():
    ret = hello("world")
    assert ret == "hello world"