import re


def contain_miner_code(content: str):
    # text search
    if content.find("stratum+") != -1:
        return True
    return False


def __is_command_safe(command):
    """
    检查命令是否仅包含安全的pip install操作。
    允许使用逻辑运算符连接的多个pip install命令。
    """
    # 拆分命令，考虑可能的逻辑运算符：||, &&, ;
    subcommands = re.split(r"\|\||&&|;", command)

    # 检查每个子命令是否都是pip install
    for subcommand in subcommands:
        if not subcommand.strip().startswith("pip install"):
            return False
    return True


"""
限制os.system调用仅包含pip install命令
"""


def contain_bad_os_exec(content: str):
    # 查找所有os.system调用
    system_calls = re.findall(r"os\.system\((.+?)\)", content)

    # 检查每个系统调用的安全性
    for call in system_calls:
        # 移除字符串两端的引号
        command = call.strip("'\"")

        # 检查命令是否安全
        if not __is_command_safe(command):
            return True

    return False
