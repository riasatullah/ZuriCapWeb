# By: Riasat Ullah

from ZuriCapWeb.utils.string_verifier import StringVerifier
from ZuriCapWeb.utils import times


def convert_int_to_string(item):
    if isinstance(item, list):
        return ','.join(str(thing) for thing in item)
    elif isinstance(item, int):
        return str(item)
    elif isinstance(item, str):
        if StringVerifier(item).is_numeric():
            return item
        else:
            return ''
    else:
        return ''


def combine_items(items: list):
    '''
    Combines a list of items into one list.
    Mainly written to put multiple ints into one list
    :param items: list of items
    :return: combined list of items
    '''
    full_list = []
    for object in items:
        if object is not None:
            if type(object) in [list, set, dict]:
                for sub_item in object:
                    full_list.append(sub_item)
            else:
                full_list.append(object)
    return full_list


def mint_reference_id(date, count, buyer_id, supplier_id):
    new_date = date[2:]
    new_count = chr(ord('A') + count-1)
    new_buyer_id = '0'*(4-len(str(buyer_id))) + str(buyer_id)
    new_supplier_id = '0' * (4 - len(str(supplier_id))) + str(supplier_id)
    return new_date + new_count + new_buyer_id + new_supplier_id


def mint_username(first_name, last_name):
    year = times.current_date()[2:4]
    username = first_name[:2] + last_name[:3] + year
    return username


def aggregate_conditions(conditions: list):
    '''
    Takes in a list of database where clauses and combines
    them into one where clause condition
    :param conditions: list of strings where clause conditions
    :return: string --> with one main where clause condition
    '''
    str_cond = ''
    if len(conditions) > 0:
        str_cond = ' where ' + ' and '.join(conditions)
    return str_cond
