from auto_complete.injection_code.torch_trainer import *
from ast import  *
import ast
from auto_complete.tool import *
from ast_checker import   AstChecker

torch_trainer_dist_code_injection_list = []
torch_trainer_trainer_code_injection_list = []

def init_transformers_injection_list():
    torch_trainer_dist_code_injection_list.clear()
    torch_trainer_trainer_code_injection_list.clear()
    torch_trainer_dist_code_injection_list.append(CodeInjectionData(0, import_expr, 0))
    torch_trainer_trainer_code_injection_list.append(CodeInjectionData(0, trainer_import_expr, 0))


class TorchTrainerHandler(ast.NodeVisitor):
    def __init__(self):
        TorchTrainerHandler.optimizer_visited = False
        TorchTrainerHandler.endline_no =  None
        self.ast_checker = AstChecker()
        self.transformers_trainer_Trainer = None

    def visit_Module(self, node: Module):

        self.transformers_trainer_Trainer = self.ast_checker.find_imported_func_name(
            node, "transformers.trainer.Trainer"
        )

        print(f'transformers_trainer_Trainer: {self.transformers_trainer_Trainer}')

        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        attr_tuple_list = [
            ('name', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        if assign_attr_name == 'train':
            TorchTrainerHandler.endline_no = node.end_lineno

        self.generic_visit(node)




    def visit_ImportFrom(self, node: ImportFrom):
        attr_tuple_list = [
            ('names', list, 1, alias),
            ('name', str),
        ]
        try:
            import_name = get_attr_recursively(node, attr_tuple_list)
        except:
            raise
        if import_name == 'NetmindTrainerCallback':
            raise DuplicateInjectionError('duplicate injection')


    def visit_keyword(self, node: keyword):
        if hasattr(node, 'arg') and node.arg == 'callbacks':

            callback_deleteion = CodeInjectionData(node.value.lineno, None, None, InjectionOperation.DELETE)
            torch_trainer_trainer_code_injection_list.append(callback_deleteion)

            trainer_injection = CodeInjectionData(node.value.lineno , trainer_expr, node.value.col_offset - 11)
            torch_trainer_trainer_code_injection_list.append(trainer_injection)

            pytorch_trainer_visited_table[trainer_expr][0] = True

        self.generic_visit(node)


    def visit_Assign(self, node):
        attr_tuple_list = [
            ('value', Call),
            ('func', Name),
            ('id', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        print(f'assign_attr_name : {assign_attr_name} node.lineno : {node.lineno}')
        if assign_attr_name == 'get_model':
            init_injection = CodeInjectionData(node.lineno, nmp_init_expr, node.col_offset)
            torch_trainer_dist_code_injection_list.append(init_injection)
            pytorch_trainer_visited_table[nmp_init_expr][0] = True

        else:
            if not TorchTrainerHandler.endline_no:
                self.generic_visit(node)
                return node

            if not self.transformers_trainer_Trainer:
                self.generic_visit(node)
                return node

            call_part = getattr(node, 'value')
            if not call_part:
                self.generic_visit(node)
                return node

            if not self.ast_checker._check_attr_or_call_stack(
                    call_part, self.transformers_trainer_Trainer):
                self.generic_visit(node)
                return node

            attr_tuple_list = [
                ('targets', list, Name),
                ('id', str)
            ]
            assigned_name = get_attr_recursively(node, attr_tuple_list)
            if not assigned_name:
                self.generic_visit(node)
                return node

            train_injection = CodeInjectionData(TorchTrainerHandler.endline_no, train_expr.format(assigned_name),
                                                node.col_offset + 4)
            torch_trainer_trainer_code_injection_list.append(train_injection)

            load_checkpoint_injection = CodeInjectionData(TorchTrainerHandler.endline_no, load_checkpoint_expr,
                                                          node.col_offset + 4)
            torch_trainer_trainer_code_injection_list.append(load_checkpoint_injection)

            pytorch_trainer_visited_table[train_expr][0] = True
            pytorch_trainer_visited_table[load_checkpoint_expr][0] = True

        self.generic_visit(node)

    def visit_ClassDef(self, node: ClassDef):
        attr_tuple_list = [
            ('name', str)
        ]

        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'CustomTrainerCallback':
            class_deletion = CodeInjectionData(node.lineno, None, None,
                                                   InjectionOperation.DELETE)
            torch_trainer_trainer_code_injection_list.append(class_deletion)

            class_injection = CodeInjectionData(node.lineno, callback_expr, node.col_offset)
            torch_trainer_trainer_code_injection_list.append(class_injection)
            pytorch_trainer_visited_table[callback_expr][0] = True
        self.generic_visit(node)



    def visit_Expr(self, node: Expr):
        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        if assign_attr_name == 'train':
            train_deleteion = CodeInjectionData(node.value.lineno, None, None, InjectionOperation.DELETE)
            torch_trainer_trainer_code_injection_list.append(train_deleteion)

        self.generic_visit(node)

