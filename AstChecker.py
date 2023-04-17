import ast
from typing import Tuple


class AstChecker:

    """
    find imported func name (or asname if exists)

    exp:
        import NetmindMixins as nm
        return nm.Netmind.nmp

        from NetmindMixins import Netmind as nd
        return nd.nmp

        from NetmindMixins.Netmind import nmp as nnmp
        return nnmp
    """

    def find_imported_func_name(self, root_node, import_path):
        import_path_array = import_path.split(".")
        possible_module_func_tuple = []
        for i in range(len(import_path_array) - 1, -1, -1):
            from_module = ".".join(import_path_array[0:i])
            import_func = import_path_array[i]
            remain_func = ".".join(import_path_array[i + 1 : len(import_path_array)])
            possible_module_func_tuple.append((from_module, import_func, remain_func))

        imported_func_name = []

        def node_name_check(possible_module_func, node):
            temp_func_name = ""
            for name in node.names:
                if name.name == possible_module_func[1]:
                    temp_func_name = possible_module_func[1]
                    if name.asname:
                        temp_func_name = name.asname
                    if possible_module_func[2]:
                        # concat module with class/function name
                        temp_func_name = temp_func_name + "." + possible_module_func[2]
            return temp_func_name

        for node in ast.walk(root_node):
            if isinstance(node, ast.Import):
                for possible_module_func in possible_module_func_tuple:
                    temp_func_name = node_name_check(possible_module_func, node)
                    if temp_func_name:
                        imported_func_name.append(temp_func_name)

            if isinstance(node, ast.ImportFrom):
                for possible_module_func in possible_module_func_tuple:
                    if possible_module_func[0] == node.module:
                        temp_func_name = node_name_check(possible_module_func, node)
                        if temp_func_name:
                            imported_func_name.append(temp_func_name)

        return imported_func_name

    """
    call_str:
        exp:    transformers.trainer.Trainer
                trainer.Trainer
                Trainer
    """

    def _check_attr_or_call_stack(self, node, call_str_list: Tuple[str]):

        # print(call_str_list[0])
        if isinstance(node, ast.Call):
            node = node.func
        for call_str in call_str_list:
            if hasattr(node, "id") and node.id == call_str:
                return True

            this_contain = True
            cur_node = node
            call_str_array = call_str.split(".")

            for i in range(len(call_str_array) - 1, -1, -1):
                id_equal = hasattr(cur_node, "id") and cur_node.id == call_str_array[i]
                attr_equal = (
                    hasattr(cur_node, "attr") and cur_node.attr == call_str_array[i]
                )
                if id_equal or attr_equal:
                    pass
                else:
                    this_contain = False
                    break

                if hasattr(cur_node, "value"):
                    cur_node = cur_node.value
                elif i > 0:
                    this_contain = False
                    break

            if this_contain:
                return True
        return False



    """
    call_str:
        exp:    transformers.trainer.Trainer
                trainer.Trainer
                Trainer
    """

    def _check_inherit(self, node, call_str_list: Tuple[str]):

        if len(node.bases) == 0:
            return False

        node = node.bases[0]
        # x = node.lineno

        for call_str in call_str_list:
            if hasattr(node, "id") and node.id == call_str:
                return True

            this_contain = True
            cur_node = node
            call_str_array = call_str.split(".")

            for i in range(len(call_str_array) - 1, -1, -1):
                id_equal = hasattr(cur_node, "id") and cur_node.id == call_str_array[i]
                attr_equal = (
                    hasattr(cur_node, "attr") and cur_node.attr == call_str_array[i]
                )
                if id_equal or attr_equal:
                    pass
                else:
                    this_contain = False
                    break

                if hasattr(cur_node, "value"):
                    cur_node = cur_node.value
                elif i > 0:
                    this_contain = False
                    break

            if this_contain:
                return True
        return False
