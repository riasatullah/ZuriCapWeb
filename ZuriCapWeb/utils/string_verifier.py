# This class verifies certain attributes of a string

import datetime
import re


class StringVerifier(object):

    def __init__(self, string: str):
        assert type(string) is str
        self.string = string

    def check_length(self, min: int, max=None):
        '''
        Checks the length of a string
        :param min: the minimum acceptable length
        :param end: the maximum acceptable length
        :return: True if length within range; False otherwise
        '''
        if max is None:
            max = min

        if min <= len(self.string) <= max:
            return True
        return False

    def contains_uppercase(self, count=1):
        '''
        Checks if a string contains uppercase letters or not
        :param count: the number of uppercase letters that
                        need to be in the string
        :return: True if contains uppercase letters;
                False otherwise
        '''
        assert count > 0
        regex = re.compile(r'^(?=(.*[A-Z].*)){0}'\
                           .format('{' + str(count) + '}'))
        try:
            regex.match(self.string).group(0)
            return True
        except Exception as e:
            return False

    def contains_lowercase(self, count=1):
        '''
        Checks if a string contains lowercase letters or not
        :param count: the number of lowercase letters that
                        need to be in the string
        :return: True if contains lowercase letters;
                False otherwise
        '''
        assert count > 0
        regex = re.compile(r'^(?=(.*[a-z].*)){0}'\
                           .format('{' + str(count) + '}'))
        try:
            regex.match(self.string).group(0)
            return True
        except Exception as e:
            return False

    def contains_digit(self, count=1):
        '''
        Checks if a string contains digits or not
        :param count: the number of digits that
                        need to be in the string
        :return: True if contains digits; False otherwise
        '''
        assert count > 0

        regex = re.compile(r'^(?=(.*\d.*)){0}'\
                           .format('{' + str(count) + '}'))
        try:
            regex.match(self.string).group(0)
            return True
        except Exception as e:
            return False

    def is_not_empty(self):
        '''
        Checks if the string is empty or not
        :return: True if not empty; False otherwise
        '''
        if len(self.string) == 0 or self.string == '':
            return False
        return True

    def date_format(self):
        '''
        Checks if the string is a date in an acceptable format or not
        :return: True if correct; False otherwise
        '''
        allowed_patterns = ['^\d{4}-\d{2}-\d{2}$',
                            '^\d{8}$']
        is_good = True
        for pattern in allowed_patterns:
            if re.match(format, self.string) is None:
                is_good = False
        return is_good

    def valid_date(self):
        '''
        Checks if a string is a valid date or not
        :return: True if it is; False otherwise
        '''
        filtered_str = self.string.replace('-', '')
        try:
            datetime.datetime.strptime(filtered_str, '%Y%m%d')
            return True
        except:
            return False

    def valid_amount(self):
        '''
        Checks if a string is a valid numeric amount or not
        :return: True if it is; False otherwise
        '''
        allowed_patterns = ['^\d{3,10}$',
                            '^\d{3,10}.\d{1,6}']
        is_good = True
        for pattern in allowed_patterns:
            if re.match(pattern, self.string) is None:
                is_good = False
        return is_good

    def is_numeric(self):
        '''
        Checks if a string is numeric or not
        :return: True if it is; False otherwise
        '''
        if re.match('(^\d+$)|(^\d+.[0-9]+$)', self.string) is None:
            return False
        else:
            return True

    def is_whole_number(self):
        '''
        Checks if a string is a whole number or not
        :return: True if it is; False otherwise
        '''
        if re.match('^\d+$', self.string) is None:
            return False
        else:
            return True

    def no_whitespace(self):
        '''
        Checks if a string has whitespace in it or not
        :return: True if it is; False otherwise
        '''
        if re.match('^.\s+.', self.string):
            return True
        else:
            return False

    def is_alphanumeric(self):
        '''
        Checks if a string is alphanumeric or not
        :return: True if it does; False otherwise
        '''
        if re.match('^\w+$', self.string):
            return True
        else:
            return False

    def valid_password(self):
        '''
        Checks if a string qualifies as a valid password or not.
        A valid password must be only alphanumeric;
        must contain at least 1 upper case letter,
        1 lower case letter and 1 number and must be at least
        8 characters in length but no more than 15.
        :return: True if it is valid; False otherwise
        '''
        if not self.check_length(8, 15):
            return False
        if not self.is_alphanumeric():
            return False
        if not self.contains_lowercase():
            return False
        if not self.contains_uppercase():
            return False
        if not self.contains_digit():
            return False
        return True

    def sql_injection(self):
        '''
        Checks if a string contains possible sql injections
        :return: True if there are sql injections; False otherwise
        '''
        key_terms = ['select', 'insert', 'update', 'delete',
                     'drop', 'alter', 'from', 'into',
                     'join', 'where']
        key_chars = [';', '*', '=', '"', "'"]
        word_list = self.string.split()
        for word in word_list:
            for separator in key_chars:
                sub_list = word.split(separator)
                if len(sub_list) > 1:
                    word_list += sub_list

        group = key_terms + key_chars
        for sql_term in group:
            if sql_term in word_list:
                return True
        return False
