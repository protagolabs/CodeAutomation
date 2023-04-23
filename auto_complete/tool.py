from ast import  *
import os

class InjectionOperation(object):
    DELETE = 1
    ADD = 2
    MODIFY = 3

class CodeInjectionData(object):
    def __init__(self, insert_line_no, insert_expr, col_offset, operation=InjectionOperation.ADD):
        self.insert_line_no = insert_line_no
        self.insert_expr = insert_expr
        self.col_offset = col_offset
        self.operation = operation

    def __repr__(self):
        return f' {self.insert_line_no},   {self.insert_expr},  {self.col_offset}, {self.operation}'


class DuplicateInjectionError(Exception):
    def __init__(self, message):
        self.message = message

class CodeNotCompliantException(Exception):
    def __init__(self, message):
        self.message = message
        pass

    def __repr__(self):
        return self.message

class CodeTemplateNotLegalException(Exception):
    def __init__(self, message):
        self.message = message
        pass

    def __repr__(self):
        return self.message

def get_attr_recursively(node, attr_tuple_list):

    raw_node = node
    for attr_tuple in attr_tuple_list:
        if len(attr_tuple) < 2:
            raise TypeError(f'Invalid attr_tuple_list tuple : {attr_tuple}')
        if not hasattr(node, attr_tuple[0]):
            return None

        node = getattr(node, attr_tuple[0])
        if attr_tuple[1] == list:
            if len(attr_tuple) == 4:
                if len(node) > attr_tuple[2]:
                    node = node[attr_tuple[2]]
            else:
                if len(node) > 0:
                    try:
                        node = node[0]
                    except:
                        raise

        attr_type = attr_tuple[len(attr_tuple) - 1]
        #attr_type = attr_tuple[2] if len(attr_tuple) == 3 else attr_tuple[1]
        if not isinstance(node, attr_type):
            return None
    return node


def sort_injection_list(injection_list):
    sorted_code_list = sorted(injection_list, key=lambda x: x.insert_line_no, reverse=True)


def get_single_return_value_name(node):
    attr_tuple_list = [
        ('targets', list, Name),
        ('id', str)
    ]
    assigned_name = get_attr_recursively(node, attr_tuple_list)
    return assigned_name



def set_visited_table(visited_table, key_list):
    """
    Decorator for function ast caller
    """
    def wrapper(func):
        def reset_visited_table_func(*args, **kwargs):
            result = func(*args, **kwargs)
            for key in key_list:
                visited_table[key][0] = True
            return result
        return reset_visited_table_func
    return wrapper


