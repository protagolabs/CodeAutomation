import ast
import re

import astor  # 如果你使用Python 3.8及以下版本


class OSSystemVisitor(ast.NodeVisitor):
    def __init__(self):
        # 初始化一个字典来跟踪模块导入及其别名
        self.import_aliases = {}
        self.safe = True
        self.imported_subprocess = False
        self.imported_system = False

    def __is_command_safe(self, command):
        """
        检查命令是否仅包含安全的pip install操作。
        允许使用逻辑运算符连接的多个pip install命令。
        """
        # 拆分命令，考虑可能的逻辑运算符：||, &&, ;
        subcommands = re.split(r"\|\||&&|;", command)

        # 检查每个子命令是否都是pip install
        for subcommand in subcommands:
            if not subcommand.strip().startswith(
                "pip install"
            ) and not subcommand.strip().startswith("pip3 install"):
                return False
        return True

    def _check_value(self, value):
        """
        递归检查值是否包含对os模块的引用。
        """
        if isinstance(value, ast.Name) and self.import_aliases.get(
            value.id, value.id
        ) in [
            "os",
            "subprocess",
        ]:
            return True
        elif isinstance(value, ast.Attribute) and self.import_aliases.get(
            value.value.id, value.value.id
        ) in [
            "os",
            "subprocess",
        ]:
            return True
        elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            return any(self._check_value(elt) for elt in value.elts)
        elif isinstance(value, ast.Dict):
            return any(self._check_value(key) for key in value.keys) or any(
                self._check_value(value) for value in value.values
            )
        return False

    def visit_Assign(self, node):
        # 检查赋值右侧是否是已知的模块别名
        if self._check_value(node.value):
            self.safe = False

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.import_aliases[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else ""
        for alias in node.names:
            self.import_aliases[alias.asname or alias.name] = f"{module}.{alias.name}"

        if node.module == "os":
            self.imported_system = True

        if node.module == "subprocess":
            self.imported_subprocess = True
        self.generic_visit(node)

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Name)
            and hasattr(node.func, "id")
            and node.func.id in self.import_aliases
        ):
            function_name = self.import_aliases[node.func.id]
            if (
                isinstance(node.func, ast.Name)
                and function_name.startswith("os")
                and function_name not in ["getenv", "environ"]
                and self.imported_system
            ) or (
                isinstance(node.func, ast.Name)
                and function_name.startswith("subprocess")
                and self.imported_subprocess
            ):
                # 适用于Python 3.9及以上
                command = astor.to_source(node.args[0]).strip()

                # 移除字符串两端的引号
                command = command.strip("'\"")

                # 检查命令是否安全
                if not self.__is_command_safe(command):
                    self.safe = False

        if (
            isinstance(node.func, ast.Attribute)
            and hasattr(node.func.value, "id")
            and node.func.value.id in self.import_aliases
        ):
            module_name = self.import_aliases[node.func.value.id]
            function_name = node.func.attr
            if (
                module_name == "os" and function_name not in ["getenv", "environ"]
            ) or module_name == "subprocess":
                # 适用于Python 3.9及以上
                command = astor.to_source(node.args[0]).strip()

                # 移除字符串两端的引号
                command = command.strip("'\"")

                # 检查命令是否安全
                if not self.__is_command_safe(command):
                    self.safe = False

        self.generic_visit(node)


"""
限制os.system调用仅包含pip install命令
"""


def contain_bad_os_exec(code):
    if code.find("tmate") != -1:
        return True

    tree = ast.parse(code)
    visitor = OSSystemVisitor()
    visitor.visit(tree)
    return not visitor.safe


def contain_miner_code(content: str):
    # text search
    if content.find("stratum+") != -1:
        return True
    return False
