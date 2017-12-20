# By: Riasat Ullah

from ZuriCapWeb.backend.database import info_queries
from ZuriCapWeb.utils.string_verifier import StringVerifier
from ZuriCapWeb.variables import params
import hashlib
import random
import string
import uuid


class Logger(object):

    credentials = dict()

    def __init__(self, username, password, id, admin=False):
        self.username = username
        self.password = password
        self.id = id
        self.admin = admin

    def get_credentials(self):
        '''
        Gets stored credentials from the database
        '''
        try:
            if self.admin:
                result = info_queries.get_admin_login(self.username)
            else:
                result = info_queries.get_login_details(self.username)
            if len(result) > 0:
                self.credentials[self.username] = result
        except Exception as e:
            raise Exception(e)

    def with_credentials(self, username, salt, hash_pwd, id_no):
        '''
        Sets provided login credentials and sets it to the class
        :param username: username of the user
        :param salt: the salt to use
        :param hash_pwd: the hash of the password
        :param id_no: the id number
        '''
        self.credentials[username] = {params.salt: salt,
                                      params.hash_password: hash_pwd,
                                      params.id: id_no}

    def is_correct(self):
        '''
        Checks if login credentials are correct or not
        :return: True if correct; False otherwise
        '''
        self.get_credentials()
        if self.is_valid(self.password):
            if self.password_matches() and self.id_matches():
                return True
        return False

    def password_matches(self):
        '''
        Checks if the password matches or not
        :return: True if it does; False otherwise
        '''
        if self.username in self.credentials:
            passport = self.credentials[self.username]
            salt = passport[params.salt]
            hash_pwd = passport[params.hash_password]
            provided_pwd_hash = self.get_hash(self.password, salt)[1]
            if hash_pwd == provided_pwd_hash:
                return True
            else:
                return False
        else:
            return False

    def id_matches(self):
        '''
        Checks if id matches or not
        :return: True if it does; False otherwise
        '''
        if self.username in self.credentials:
            passport = self.credentials[self.username]
            id_no = passport[params.id]
            if not self.admin:
                id_no = id_no[-4:]
            if id_no == self.id:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def get_hash(password, salt=None):
        '''
        Gets the hash of a password
        :param password: the password
        :param salt: the salt to be used; if none is provided a new salt will be created
        :return: tuple --> (salt, hashed_password)
        '''
        if salt is None:
            salt = uuid.uuid4().hex
        hash_password = hashlib.sha512(password.encode('utf-8') +
                                       salt.encode('utf-8')).hexdigest()
        return (salt, hash_password)

    @staticmethod
    def generate_password():
        '''
        Generates a random password
        :return: a new password
        '''
        pwd_length = random.randint(11, 16)
        options = {0: list(string.ascii_lowercase)[random.randint(0, 26)],
                   1: list(string.ascii_uppercase)[random.randint(0, 26)],
                   2: random.randint(0, 10)}
        pwd = ''
        for i in range(0, pwd_length + 1):
            pwd += options[random.randint(0, 3)]
        return pwd

    @staticmethod
    def is_valid(password):
        '''
        Checks if a password fits the valid criterias or not
        :param password: password
        :return: True if it is valid; False otherwise
        '''
        password = StringVerifier(password)
        if password.valid_password():
            return True
        else:
            return False
