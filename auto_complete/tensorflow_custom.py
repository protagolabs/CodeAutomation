from auto_complete.injection_code.tensorflow_custom import *
from ast import  *
from auto_complete.tool import *
import  ast

tf_custom_code_injection_list = []
def init_custom_tf_injection_list():
    tf_custom_code_injection_list.clear()
    tf_custom_code_injection_list.append(CodeInjectionData(0, import_expr, 0))



class TensorflowCustomHandler(NodeVisitor):

    def __init__(self):
        TensorflowCustomHandler.out_loop_visited = False
        TensorflowCustomHandler.inner_loop_train_visited = False
        TensorflowCustomHandler.inner_loop_val_visited = False

        TensorflowCustomHandler.visit_if_key_list = [finish_training_expr]
        TensorflowCustomHandler.visit_assign_key_list = [nmp_init_expr]
        TensorflowCustomHandler.visit_for_key_list = [model_distibuted_expr, init_train_bar_expr,
                             init_eval_bar_expr, should_skip_expr,
                             step_expr, evaluate_expr]


    def visit_ImportFrom(self, node: ImportFrom):
        attr_tuple_list = [
            ('names', list, alias),
            ('name', str),
        ]
        import_name = get_attr_recursively(node, attr_tuple_list)
        if import_name == 'nmp':
            raise DuplicateInjectionError('duplicate injection')


    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Add):
            node.op = ast.Sub()
        self.generic_visit(node)

    def visit_If(self, node):
        attr_tuple_list = [
            ('test', Compare),
            ('comparators', list, ast.Constant),
            ('value', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        if assign_attr_name == '__main__':
            finish_injection = CodeInjectionData(node.end_lineno, finish_training_expr, node.col_offset + 4)
            tf_custom_code_injection_list.append(finish_injection)
            tensorflow_custom_visited_table[finish_training_expr][0] = True

        elif assign_attr_name == 0:
            attr_tuple_list = [
                ('body', list, Expr),
                ('value', Call),
                ('func', Attribute),
                ('attr', str)
            ]
            assign_attr_name = get_attr_recursively(node, attr_tuple_list)
            if assign_attr_name == 'save':
                for index in range(node.lineno, node.end_lineno + 1):
                    save_point_deleteion = CodeInjectionData(index, None, None, InjectionOperation.DELETE)
                    tf_custom_code_injection_list.append(save_point_deleteion)
        self.generic_visit(node)

    def visit_Assign(self, node):
        attr_tuple_list = [
            ('value', ast.Call),
            ('func', ast.Attribute),
            ('attr', str)
        ]

        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        print(f'assign_attr_name : {assign_attr_name} node.lineno : {node.lineno}')
        if assign_attr_name == 'MultiWorkerMirroredStrategy':
            nmp_init_injection = CodeInjectionData(node.lineno, nmp_init_expr, node.col_offset)
            tf_custom_code_injection_list.append(nmp_init_injection)
            tensorflow_custom_visited_table[nmp_init_expr][0] = True


        self.generic_visit(node)

    def visit_For(self, node: For):
        if not TensorflowCustomHandler.out_loop_visited :
            id_tuple_list = [
                ('target', ast.Name),
                ('id', str),
            ]
            assign_attr_name = get_attr_recursively(node, id_tuple_list)
            if assign_attr_name != 'epoch':
                self.generic_visit(node)
                return node

            TensorflowCustomHandler.out_loop_visited = True
            model_distribute_injection = CodeInjectionData(node.lineno - 1, model_distibuted_expr, node.col_offset)
            init_train_bar_injection = CodeInjectionData(node.lineno - 1, init_train_bar_expr, node.col_offset)
            init_eval_bar_injection = CodeInjectionData(node.lineno - 1, init_eval_bar_expr, node.col_offset)

            tf_custom_code_injection_list.append(init_train_bar_injection)
            tf_custom_code_injection_list.append(init_eval_bar_injection)
            tf_custom_code_injection_list.append(model_distribute_injection)

            tensorflow_custom_visited_table[model_distibuted_expr][0] = True
            tensorflow_custom_visited_table[init_train_bar_expr][0] = True
            tensorflow_custom_visited_table[init_eval_bar_expr][0] = True

            self.generic_visit(node)
            return node

        if not  TensorflowCustomHandler.inner_loop_train_visited:
            id_tuple_list = [
                ('target', ast.Name),
                ('id', str),
            ]
            assign_attr_name = get_attr_recursively(node, id_tuple_list)
            if assign_attr_name != 'ds':
                self.generic_visit(node)
                return node

            TensorflowCustomHandler.inner_loop_train_visited = True
            skip_injection = CodeInjectionData(node.lineno, should_skip_expr, node.col_offset + 4)
            tf_custom_code_injection_list.append(skip_injection)

            step_injection = CodeInjectionData(node.end_lineno, step_expr, node.col_offset + 4)
            tf_custom_code_injection_list.append(step_injection)

            tensorflow_custom_visited_table[should_skip_expr][0] = True
            tensorflow_custom_visited_table[step_expr][0] = True

            self.generic_visit(node)
            return node

        if not TensorflowCustomHandler.inner_loop_val_visited:
            id_tuple_list = [
                ('iter', ast.Call),
                ('args', list, ast.Name),
                ('id', str),
            ]
            assign_attr_name = get_attr_recursively(node, id_tuple_list)
            if assign_attr_name != 'test_data_iterator':
                self.generic_visit(node)
                return node

            TensorflowCustomHandler.inner_loop_val_visited = True
            eval_injection = CodeInjectionData(node.end_lineno, evaluate_expr, node.col_offset)
            tf_custom_code_injection_list.append(eval_injection)
            tensorflow_custom_visited_table[evaluate_expr][0] = True
            self.generic_visit(node)
            return node
        self.generic_visit(node)


