from auto_complete.injection_code.torch_custom_without_eval import *
from ast import  *
import ast
from  auto_complete.tool import *

torch_no_eval_dist_code_injection_list = []
torch_no_eval_trainer_code_injection_list = []



torch_no_eval_dist_code_injection_list.append(CodeInjectionData(0, import_expr, 0))
torch_no_eval_trainer_code_injection_list.append(CodeInjectionData(0, nmp_import_expr, 0))


class TorchCustomWithOutEvalTrainDistHandler(ast.NodeVisitor):
    outer_loop_visited = False
    end_if_block_last_line = -1
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

    def visit_If(self, node):
        attr_tuple_list = [
            ('test', Compare),
            ('comparators', list, Constant),
            ('value', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        print(f'assign_attr_name : {assign_attr_name} node.lineno : {node.lineno}')
        if assign_attr_name == '__main__':
            finish_training_injection = CodeInjectionData(node.end_lineno, finish_training_expr, node.col_offset + 4)
            torch_no_eval_dist_code_injection_list.append(finish_training_injection)
            pytorch_mlm_custom_visited_table[finish_training_expr][0] = True
        self.generic_visit(node)

    def visit_Assign(self, node):

        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'DistributedDataParallel':
            dist_model_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            torch_no_eval_dist_code_injection_list.append(dist_model_deletion)

            model_name = model_distibuted_expr.format(TorchCustomWithOutEvalTrainDistHandler.model_name)
            distributed_model_injection = CodeInjectionData(node.lineno, model_name, node.col_offset)
            torch_no_eval_dist_code_injection_list.append(distributed_model_injection)
            pytorch_mlm_custom_visited_table[model_distibuted_expr][0] = True
        else:
            fun_name_tuple_list = [
                ('value', Call),
                ('func', Name),
                ('id', str)
            ]
            attr_name = get_attr_recursively(node, fun_name_tuple_list)
            if attr_name == 'get_optimizer':
                optimizer_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
                torch_no_eval_dist_code_injection_list.append(optimizer_deletion)

                optimizer_attr = get_single_return_value_name(node)
                optimer_name = optimizer_init_train_expr.format(optimizer_attr, TorchCustomWithOutEvalTrainDistHandler.dataloader_name)
                optimizer_injection = CodeInjectionData(node.lineno + 1, optimer_name, node.col_offset)
                torch_no_eval_dist_code_injection_list.append(optimizer_injection)
                pytorch_mlm_custom_visited_table[optimizer_init_train_expr][0] = True
            elif attr_name == 'DistributedSampler':
                init_injection = CodeInjectionData(node.lineno - 1, nmp_init_expr, node.col_offset)

                torch_no_eval_dist_code_injection_list.append(init_injection)
                pytorch_mlm_custom_visited_table[nmp_init_expr][0] = True
            elif attr_name == 'get_model':
                attr_tuple_list = [
                    ('targets', list, Tuple),
                    ('elts', list, Name),
                    ('id', str)
                ]
                TorchCustomWithOutEvalTrainDistHandler.model_name = get_attr_recursively(node, attr_tuple_list)

            elif attr_name == 'DataLoader':
                attr_name = get_single_return_value_name(node)
                TorchCustomWithOutEvalTrainDistHandler.dataloader_name = attr_name


        self.generic_visit(node)

    def visit_Expr(self, node):
        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        assign_attr_name = get_attr_recursively(node, attr_tuple_list)
        print(f'assign_attr_name : {assign_attr_name} node.lineno : {node.lineno}')

        if assign_attr_name == 'init_process_group':
            init_backend_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            torch_no_eval_dist_code_injection_list.append(init_backend_deletion)
        self.generic_visit(node)



class TorchCustomWithOutEvalTrainerHandler(ast.NodeVisitor):
    outer_loop_visited = False
    end_if_block_last_line = -1

    def visit_ImportFrom(self, node: ImportFrom):
        attr_tuple_list = [
            ('names', list, alias),
            ('name', str),
        ]
        import_name = get_attr_recursively(node, attr_tuple_list)
        if import_name == 'nmp':
            raise DuplicateInjectionError('duplicate injection')


    def visit_For(self, node: For):

        if not TorchCustomWithOutEvalTrainerHandler.outer_loop_visited:
            outloop_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            torch_no_eval_trainer_code_injection_list.append(outloop_deletion)

            attr_tuple_list = [
                ('target', Name),
                ('id', str)
            ]
            attr_name = get_attr_recursively(node, attr_tuple_list)

            if attr_name:
                current_epoch_injection = CodeInjectionData(node.lineno - 1, cur_epoch_expr.format(attr_name), node.col_offset)
                torch_no_eval_trainer_code_injection_list.append(current_epoch_injection)
                pytorch_mlm_custom_visited_table[cur_epoch_expr][0] = True

                outer_loop_injection = CodeInjectionData(node.lineno, outer_loop_expr.format(attr_name, attr_name), node.col_offset)
                torch_no_eval_trainer_code_injection_list.append(outer_loop_injection)
                pytorch_mlm_custom_visited_table[outer_loop_expr][0] = True

                TorchCustomWithOutEvalTrainerHandler.outer_loop_visited = True
                print(f'TorchCustomVisitor.outer_loop_visited : {TorchCustomWithOutEvalTrainerHandler.outer_loop_visited}')
        else:
            #innerloop_deletion = CodeInjectionData(node.lineno, None, None, InjectionOperation.DELETE)
            #torch_no_eval_trainer_code_injection_list.append(innerloop_deletion)

            torch_trainer_inner_loop_list = [
                (node.lineno + 1, should_skip_expr, node.col_offset + 4),
                (node.end_lineno, step_expr, node.col_offset + 4),
                #(node.end_lineno + 1, save_pretrained_expr, node.col_offset + 4)
            ]
            for inner_loop_meta_data in torch_trainer_inner_loop_list:
                injection = CodeInjectionData(inner_loop_meta_data[0], inner_loop_meta_data[1],
                                              inner_loop_meta_data[2])
                torch_no_eval_trainer_code_injection_list.append(injection)

            pytorch_mlm_custom_visited_table[should_skip_expr][0] = True
            pytorch_mlm_custom_visited_table[step_expr][0] = True

        self.generic_visit(node)

