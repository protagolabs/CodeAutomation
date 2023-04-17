from JobCommon.auto_complete.injection_code.hivemind_trainer import *
from ast import  *
from JobCommon.auto_complete.tool import *

hm_mlm_callback_code_injection_list = []
hm_mlm_training_monitor_code_injection_list = []

hm_mlm_callback_code_injection_list.append(CodeInjectionData(0, callback_import, 0))
hm_mlm_training_monitor_code_injection_list.append(CodeInjectionData(0, training_monitor_import_expr, 0))


class HivemindCallbackMonitorHandler(NodeVisitor):
    def visit_ClassDef(self, node: ClassDef):
        attr_tuple_list = [
            ('name', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'CollaborativeCallback':
            class_deletion = CodeInjectionData(node.lineno, None, None,
                                                   InjectionOperation.DELETE)
            hm_mlm_callback_code_injection_list.append(class_deletion)

            class_injection = CodeInjectionData(node.lineno, class_expr, node.col_offset)
            hm_mlm_callback_code_injection_list.append(class_injection)
        self.generic_visit(node)

    def visit_Expr(self, node: Expr):
        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == '__init__':
            init_deletion = CodeInjectionData(node.lineno, None, None,
                                               InjectionOperation.DELETE)
            hm_mlm_callback_code_injection_list.append(init_deletion)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        attr_tuple_list = [
            ('name', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == '__init__':
            init_injection = CodeInjectionData(node.end_lineno, init_expr, node.col_offset + 4)
            hm_mlm_callback_code_injection_list.append(init_injection)

        self.generic_visit(node)

"""
class HivemindMlmMonitorHandler(NodeVisitor):


    def visit_Assign(self, node: Assign):
        attr_tuple_list = [
            ('value', Call),
            ('func', Name),
            ('id', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)

        if attr_name == 'get_model':
            id_tuple_list = [
                ('targets', list, Tuple),
                ('elts', list, Attribute),
                ('value', Name),
                ('id', str)
            ]
            id_name = get_attr_recursively(node, id_tuple_list)

            attr_tuple_list = [
                ('targets', list, Tuple),
                ('elts', list, Attribute),
                ('attr', str)
            ]
            attr_name = get_attr_recursively(node, attr_tuple_list)
            print(f'concatenate {id_name} and {attr_name}')
            model_pattern = id_name + '.' + attr_name
            model_expr = netmind_model_expr.format(model_pattern, model_pattern)

            netmind_model_injection = CodeInjectionData(node.lineno, model_expr, node.col_offset)
            hm_mlm_training_monitor_code_injection_list.append(netmind_model_injection)

        else:
            attr_tuple_list = [

                ('value', Call),
                ('func', Attribute),
                ('attr', str)
            ]
            attr_name = get_attr_recursively(node, attr_tuple_list)
            if attr_name == 'DHT':
                init_injection = CodeInjectionData(node.end_lineno, hmp_init_expr, node.col_offset)
                hm_mlm_training_monitor_code_injection_list.append(init_injection)
            elif attr_name == "get_optimizer":

                assigned_name = get_single_return_value_name(node)
                formatted_expr = optimizer_expr.format(assigned_name, assigned_name)
                opt_injection = CodeInjectionData(node.lineno, formatted_expr, node.col_offset)
                hm_mlm_training_monitor_code_injection_list.append(opt_injection)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        attr_tuple_list = [
            ('name', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'upload_checkpoint':
            save_injection = CodeInjectionData(node.lineno, hmp_save_pretrained_expr, node.col_offset + 4)
            hm_mlm_training_monitor_code_injection_list.append(save_injection)


        self.generic_visit(node)

    def visit_While(self, node: While):
        step_injection = CodeInjectionData(node.end_lineno, hmp_step_expr, node.col_offset + 4)
        hm_mlm_training_monitor_code_injection_list.append(step_injection)
        self.generic_visit(node)
"""

