# By: Riasat Ullah

import pandas


def total_from_dict(data_dict, key_name):
    '''
    Calculates the total value of an
    attribute in a dictionary
    :param data_dict: the dictionary
    :param key_name: attribute
    :return: total value (float)
    '''
    frame = pandas.DataFrame(data_dict)
    total = frame[key_name].sum()
    return float(total)


def min_from_dict(data_dict, key_name):
    '''
    Finds the minimum value of an
    attribute in a dictionary
    :param data_dict: the dictionary
    :param key_name: attribute
    :return: minimum value
    '''
    frame = pandas.DataFrame(data_dict)
    minimum = frame[key_name].min()
    return minimum
