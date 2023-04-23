
from auto_complete.injection_code.tensorflow_trainer import *
from ast import  *
import ast
from auto_complete.tool import *

tf_trainer_code_injection_list = []

tf_trainer_code_injection_list.append(CodeInjectionData(0, import_insert_line_expr, 0))


class TensorflowTrainerHandler(NodeVisitor):

    fit_args_body = []

    def visit_ImportFrom(self, node: ImportFrom):
        attr_tuple_list = [
            ('names', list, alias),
            ('name', str),
        ]
        import_name = get_attr_recursively(node, attr_tuple_list)
        if import_name == 'TensorflowTrainerCallback':
            raise DuplicateInjectionError('duplicate injection')


    def visit_ClassDef(self, node: ClassDef):
        attr_tuple_list = [
            ('name', str),

        ]
        value_name = get_attr_recursively(node, attr_tuple_list)
        if value_name == 'CustomTrainerCallback':
            class_deletion = CodeInjectionData(node.lineno, None, None,
                                               InjectionOperation.DELETE)
            tf_trainer_code_injection_list.append(class_deletion)

            class_injection = CodeInjectionData(node.lineno, callback_insert_expr, node.col_offset)
            tf_trainer_code_injection_list.append(class_injection)
            tensorflow_trainer_visited_table[callback_insert_expr][0] = True
        self.generic_visit(node)


    def visit_Assign(self, node: Assign):
        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        value_name = get_attr_recursively(node, attr_tuple_list)
        if value_name == 'fit':
            fit_call_back_injection = CodeInjectionData(node.lineno - 1, fit_call_back_insert_expr, node.col_offset)
            tf_trainer_code_injection_list.append(fit_call_back_injection)
            tensorflow_trainer_visited_table[fit_call_back_insert_expr][0] = True
        self.generic_visit(node)

    def visit_keyword(self, node: keyword):
        if hasattr(node, 'arg'):
            if node.arg == 'callbacks':
                callback_deleteion = CodeInjectionData(node.value.lineno, None, None, InjectionOperation.DELETE)
                tf_trainer_code_injection_list.append(callback_deleteion)

                callback_injection = CodeInjectionData(node.value.lineno, all_back_expr, node.value.col_offset - 8 )
                tf_trainer_code_injection_list.append(callback_injection)
                tensorflow_trainer_visited_table[all_back_expr][0] = True

        self.generic_visit(node)


