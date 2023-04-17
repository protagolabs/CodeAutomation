from auto_complete.injection_code.torch_custom_with_eval import *
from ast import  *
import ast
from auto_complete.tool import *

torch_cus_eval_dist_code_injection_list = []
torch_cus_eval_trainer_code_injection_list = []



torch_cus_eval_dist_code_injection_list.append(CodeInjectionData(0, import_expr, 0))
torch_cus_eval_trainer_code_injection_list.append(CodeInjectionData(0, nmp_import_expr, 0))



class TorchCustomWithEvalTrainDistHandler(ast.NodeVisitor):
    outer_loop_visited = False
    model_name = None
    dataloader_name = None

    def visit_ImportFrom(self, node: ImportFrom):

        attr_tuple_list = [
            ('names', list, alias),
            ('name', str),
        ]
        import_name = get_attr_recursively(node, attr_tuple_list)
        if import_name == 'nmp':
            raise DuplicateInjectionError('duplicate injection')
        self.generic_visit(node)

    def visit_Assign(self, node: Assign):

        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'DistributedDataParallel':
            dist_model_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            torch_cus_eval_dist_code_injection_list.append(dist_model_deletion)

            model_name = model_distibuted_expr.format(TorchCustomWithEvalTrainDistHandler.model_name)
            distributed_model_injection = CodeInjectionData(node.lineno, model_name, node.col_offset)
            torch_cus_eval_dist_code_injection_list.append(distributed_model_injection)
            pytorch_resnet_custom_visited_table[model_distibuted_expr][0] = True

        else:
            fun_name_tuple_list = [
                ('value', Call),
                ('func', Name),
                ('id', str)
            ]
            attr_name = get_attr_recursively(node, fun_name_tuple_list)
            if attr_name == 'get_optimizer':
                optimizer_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
                torch_cus_eval_dist_code_injection_list.append(optimizer_deletion)

                optimizer_name = optimizer_expr.format(get_single_return_value_name(node))
                optimizer_injection = CodeInjectionData(node.lineno + 1, optimizer_name, node.col_offset)
                torch_cus_eval_dist_code_injection_list.append(optimizer_injection)

                init_train_name = init_train_bar_expr.format(TorchCustomWithEvalTrainDistHandler.dataloader_name)
                init_train_injection = CodeInjectionData(node.lineno + 2, init_train_name, node.col_offset)
                torch_cus_eval_dist_code_injection_list.append(init_train_injection)
                init_eval_injection = CodeInjectionData(node.lineno + 3, init_eval_bar_expr, node.col_offset)
                torch_cus_eval_dist_code_injection_list.append(init_eval_injection)

                pytorch_resnet_custom_visited_table[optimizer_expr][0] = True
                pytorch_resnet_custom_visited_table[init_train_bar_expr][0] = True
                pytorch_resnet_custom_visited_table[init_eval_bar_expr][0] = True

            elif attr_name == 'DistributedSampler':
                init_injection = CodeInjectionData(node.lineno - 1, nmp_init_expr, node.col_offset)

                torch_cus_eval_dist_code_injection_list.append(init_injection)
                pytorch_resnet_custom_visited_table[nmp_init_expr][0] = True

            elif attr_name == 'get_model':
                attr_tuple_list = [
                    ('targets', list, Name),
                    ('id', str)
                ]
                TorchCustomWithEvalTrainDistHandler.model_name = get_attr_recursively(node, attr_tuple_list)
            elif attr_name == 'DataLoader':
                if not TorchCustomWithEvalTrainDistHandler.dataloader_name :
                    attr_name = get_single_return_value_name(node)
                    TorchCustomWithEvalTrainDistHandler.dataloader_name = attr_name


        self.generic_visit(node)

    def visit_Expr(self, node):

        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        if assign_attr_name == 'init_process_group':
            init_process_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            torch_cus_eval_dist_code_injection_list.append(init_process_deletion)

        self.generic_visit(node)

    def visit_If(self, node):
        attr_tuple_list = [
            ('test', Compare),
            ('comparators', list, Constant),
            ('value', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        if assign_attr_name == '__main__':
            finish_injection = CodeInjectionData(node.end_lineno, finish_training_expr, node.col_offset)
            torch_cus_eval_dist_code_injection_list.append(finish_injection)
            pytorch_resnet_custom_visited_table[finish_training_expr][0] = True
        self.generic_visit(node)

class TorchCustomWithEvalTrainerHandler(ast.NodeVisitor):
    train_func_visited = False
    train_func_visited_finished = False
    outer_loop_visited = False
    for_loop_finished = False

    def visit_ImportFrom(self, node: ImportFrom):

        attr_tuple_list = [
            ('names', list, alias),
            ('name', str),
        ]
        import_name = get_attr_recursively(node, attr_tuple_list)
        if import_name == 'nmp':
            raise DuplicateInjectionError('duplicate injection')
        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef) :
        attr_tuple_list = [
            ('name', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        if assign_attr_name == 'validate':
            validate_injection = CodeInjectionData(node.end_lineno -1  , evaluate_expr,
                                                        node.col_offset + 4)
            torch_cus_eval_trainer_code_injection_list.append(validate_injection)
            pytorch_resnet_custom_visited_table[evaluate_expr][0] = True
        elif assign_attr_name == 'train':
            TorchCustomWithEvalTrainerHandler.train_func_visited = True
        self.generic_visit(node)


    def visit_For(self, node: For):
        if TorchCustomWithEvalTrainerHandler.for_loop_finished:
            print('l will jump out ')
            self.generic_visit(node)
            return node

        if not TorchCustomWithEvalTrainerHandler.train_func_visited:

            self.generic_visit(node)
            return node

        if not TorchCustomWithEvalTrainerHandler.outer_loop_visited:
            outloop_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            torch_cus_eval_trainer_code_injection_list.append(outloop_deletion)

            attr_tuple_list = [
                ('target', Name),
                ('id', str)
            ]
            attr_name = get_attr_recursively(node, attr_tuple_list)

            if attr_name:
                current_epoch_injection = CodeInjectionData(node.lineno - 1, cur_epoch_expr.format(attr_name),
                                                            node.col_offset)
                torch_cus_eval_trainer_code_injection_list.append(current_epoch_injection)

                outer_loop_injection = CodeInjectionData(node.lineno, outer_loop_expr.format(attr_name, attr_name),
                                                         node.col_offset)
                torch_cus_eval_trainer_code_injection_list.append(outer_loop_injection)

                TorchCustomWithEvalTrainerHandler.outer_loop_visited = True
                print(
                    f'TorchCustomVisitor.outer_loop_visited : {TorchCustomWithEvalTrainerHandler.outer_loop_visited}')
                pytorch_resnet_custom_visited_table[cur_epoch_expr][0] = True
                pytorch_resnet_custom_visited_table[outer_loop_expr][0] = True
        else:

            torch_trainer_inner_loop_list = [
                (node.lineno , should_skip_expr, node.col_offset + 4),
                (node.lineno + 1, continue_expr, node.col_offset + 8),

                (node.end_lineno, step_expr, node.col_offset + 4),
                #(node.end_lineno + 1, save_pretrained_expr, node.col_offset + 4)
            ]
            for inner_loop_meta_data in torch_trainer_inner_loop_list:
                injection = CodeInjectionData(inner_loop_meta_data[0], inner_loop_meta_data[1],
                                              inner_loop_meta_data[2])
                torch_cus_eval_trainer_code_injection_list.append(injection)

            TorchCustomWithEvalTrainerHandler.for_loop_finished = True

            pytorch_resnet_custom_visited_table[should_skip_expr][0] = True
            pytorch_resnet_custom_visited_table[continue_expr][0] = True
            pytorch_resnet_custom_visited_table[step_expr][0] = True

        self.generic_visit(node)

