
from auto_complete.injection_code.hivemind_custom import *
from ast import *
from auto_complete.tool import *

hm_resnet_optimizer_injection_list = []
hm_resnet_run_hm_resnet_trainer_injection_list = []
hm_resnet_training_monitor_code_injection_list = []
hm_resnet_trainer_injection_list = []

hm_resnet_optimizer_injection_list.append(CodeInjectionData(0, optimizer_htp_expr, 0))
hm_resnet_run_hm_resnet_trainer_injection_list.append(CodeInjectionData(0, run_trainer_htpimport_expr, 0))
hm_resnet_training_monitor_code_injection_list.append(CodeInjectionData(0, training_monitor_import_expr, 0))
hm_resnet_trainer_injection_list.append(CodeInjectionData(0, trainer_import, 0))

injection_list_collection = [
    hm_resnet_run_hm_resnet_trainer_injection_list,
    hm_resnet_optimizer_injection_list,
    hm_resnet_trainer_injection_list,
    hm_resnet_training_monitor_code_injection_list
]

from auto_complete.injection_code.hivemind_custom import *
from ast import *
from auto_complete.tool import *


class HivemindResnetOptimizerHandler(NodeVisitor):
    get_optimizer_end_line_no = None
    dht_name = None
    optimizer_name = None
    local_pubkey_name = None



    def visit_Assign(self, node: Assign):
        attr_tuple_list = [
            ('value', Call),
            ('func', Attribute),
            ('attr', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'make_validators':
            attr_tuple_list = [
                ('targets', list, Tuple),
                ('elts', list, 1, Name),
                ('id', str)
            ]
            HivemindResnetOptimizerHandler.local_pubkey_name = get_attr_recursively(node, attr_tuple_list)
        else:
            attr_tuple_list = [
                ('value', Call),
                ('func', Name),
                ('id', str)
            ]
            attr_name = get_attr_recursively(node, attr_tuple_list)
            attr_tuple_list = [
                ('targets', list, Name),
                ('id', str)
            ]
            if attr_name == 'Optimizer':
                HivemindResnetOptimizerHandler.optimizer_name = get_attr_recursively(node, attr_tuple_list)
            elif attr_name == 'DHT':
                HivemindResnetOptimizerHandler.dht_name = get_attr_recursively(node, attr_tuple_list)

        self.generic_visit(node)

    def visit_Return(self, node: Return):
        init_expr = htp_init_expr.format(HivemindResnetOptimizerHandler.dht_name,
                                         HivemindResnetOptimizerHandler.optimizer_name, \
                                         HivemindResnetOptimizerHandler.local_pubkey_name)
        htp_init_injection = CodeInjectionData(node.lineno - 1, init_expr, node.col_offset)
        hm_resnet_optimizer_injection_list.append(htp_init_injection)
        self.generic_visit(node)


class HivemindResnetRunTrainerHandler(NodeVisitor):

    def visit_If(self, node: If):
        attr_tuple_list = [
            ('test', Compare),
            ('comparators', list, Constant),
            ('value', str),
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == '__main__':
            htp_end_train_injection = CodeInjectionData(node.end_lineno, htp_train_end, node.col_offset + 4)
            hm_resnet_run_hm_resnet_trainer_injection_list.append(htp_end_train_injection)
        self.generic_visit(node)

    def visit_Assign(self, node: Assign):

        attr_tuple_list = [
            ('value', Call),
            ('func', Name),
            ('id', str),
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'get_model':
            model_name = get_single_return_value_name(node)
            if not model_name:
                model_tuple_list = [
                    ('targets', list, Tuple),
                    ('elts', list, Name),
                    ('id', str)
                ]
                model_name = get_attr_recursively(node, model_tuple_list)
                if not model_name:
                    raise Exception(f'get model name failed')

            model_expr = netmind_model_expr.format(model_name, model_name)

            netmind_model_injection = CodeInjectionData(node.lineno, model_expr, node.col_offset)
            hm_resnet_run_hm_resnet_trainer_injection_list.append(netmind_model_injection)
        self.generic_visit(node)


"""
class HivemindResnetMonitorHandler(NodeVisitor):
    model_pattern = None
    dht_name = None
    local_pubkey_name = None

    def visit_Assign(self, node: Assign):

        attr_tuple_list = [
            ('value', Call),
            ('func', Name),
            ('id', str),
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
            if not id_name:
                id_tuple_list = [
                    ('targets', list, Attribute),
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
            if not attr_name:
                attr_tuple_list = [
                    ('targets', list, Attribute),
                    ('attr', str)
                ]
                attr_name = get_attr_recursively(node, attr_tuple_list)
            print(f'concatenate {id_name} and {attr_name}')
            HivemindResnetMonitorHandler.model_pattern = id_name + '.' + attr_name
            model_expr = netmind_model_expr.format(HivemindResnetMonitorHandler.model_pattern,
                                                   HivemindResnetMonitorHandler.model_pattern)

            netmind_model_injection = CodeInjectionData(node.lineno, model_expr, node.col_offset)
            hm_resnet_training_monitor_code_injection_list.append(netmind_model_injection)
        else:
            attr_tuple_list = [
                ('value', Call),
                ('func', Attribute),
                ('attr', str),
            ]
            attr_name = get_attr_recursively(node, attr_tuple_list)
            if attr_name == 'DHT':
                attr_tuple_list = [
                    ('targets', list, Name),
                    ('id', str),
                ]

                HivemindResnetMonitorHandler.dht_name = get_attr_recursively(node, attr_tuple_list)
                init_expr = hmp_init_expr.format(HivemindResnetMonitorHandler.dht_name,
                                                 HivemindResnetMonitorHandler.local_pubkey_name)
                htp_init_injection = CodeInjectionData(node.end_lineno, init_expr, node.col_offset)
                hm_resnet_training_monitor_code_injection_list.append(htp_init_injection)

            elif attr_name == 'make_validators':
                attr_tuple_list = [
                    ('targets', list, Tuple),
                    ('elts', list, 1, Name),
                    ('id', str)
                ]
                HivemindResnetMonitorHandler.local_pubkey_name = get_attr_recursively(node, attr_tuple_list)
            elif attr_name == "get_optimizer":


                assigned_name = get_single_return_value_name(node)

                formatted_optimizer_expr = optimizer_expr.format(assigned_name, assigned_name)
                opt_injection = CodeInjectionData(node.lineno, formatted_optimizer_expr, node.col_offset)
                hm_resnet_training_monitor_code_injection_list.append(opt_injection)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        attr_tuple_list = [
            ('name', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'upload_checkpoint':
            save_pretrain__injection = CodeInjectionData(node.lineno, hmp_save_pretrained_expr, node.col_offset + 4)
            hm_resnet_training_monitor_code_injection_list.append(save_pretrain__injection)
        self.generic_visit(node)


    def visit_While(self, node: While):
        step_injection = CodeInjectionData(node.end_lineno, hmp_step_expr, node.col_offset + 4)
        hm_resnet_training_monitor_code_injection_list.append(step_injection)
        self.generic_visit(node)
"""



class HivemindResnetTrainerHandler(NodeVisitor):
    train_func_end_lineno = None
    for_count = 0

    def insert_htp_end(self, node):
        htp_end_tuple_list = [
            (htp_step_end_exit, 8),
            (htp_step_end_shut, 12),
            (htp_step_end_inner_if, 8),
            (htp_step_end_comment, 8),
            (htp_step_end_if, 4),
        ]
        if HivemindResnetTrainerHandler.for_count == 2:
            for index in range(len(htp_end_tuple_list)):
                hm_resnet_trainer_injection_list.pop()

        for index, htp_tuple in enumerate(htp_end_tuple_list):
            insert = CodeInjectionData(node.end_lineno, htp_tuple[0], node.col_offset + htp_tuple[1])
            hm_resnet_trainer_injection_list.append(insert)

        return

    def visit_For(self, node: For):
        if node.lineno >= HivemindResnetTrainerHandler.train_func_end_lineno:
            self.generic_visit(node)
            return node
        HivemindResnetTrainerHandler.for_count += 1


        if HivemindResnetTrainerHandler.for_count == 1:
            htp_set_batch_size_steps_injection = CodeInjectionData(node.lineno - 1, htp_set_batch_size_steps,
                                                                   node.col_offset)
            hm_resnet_trainer_injection_list.append(htp_set_batch_size_steps_injection)

            htp_step_begin_injection = CodeInjectionData(node.lineno, htp_step_begin, node.col_offset + 4)
            hm_resnet_trainer_injection_list.append(htp_step_begin_injection)

        self.insert_htp_end(node)
        self.generic_visit(node)


    def visit_FunctionDef(self, node: FunctionDef):
        attr_tuple_list = [
            ('name', str)
        ]
        attr_name = get_attr_recursively(node, attr_tuple_list)
        if attr_name == 'train':
            HivemindResnetTrainerHandler.train_func_end_lineno = node.end_lineno
        self.generic_visit(node)


