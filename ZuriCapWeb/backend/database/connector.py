# By: Riasat Ullah

from ZuriCapWeb.variables import messages
import psycopg2


class DBConn(object):

    def __init__(self):
        self.conn = self.connect()

    @staticmethod
    def connect():
        '''
        Creates a database connection
        :return: connection
        '''
        try:
            #conn = psycopg2.connect("dbname='access-test' user='postgres' host='localhost' password='iamriasat12'")
            conn = psycopg2.connect("dbname='access_main' user='zuricap'" +\
                                    "host='zuricap-access-db.cvg3qh53tpik.eu-west-2.rds.amazonaws.com'" +\
                                    "password='Access1234' port='5432'")
            return conn
        except psycopg2.DatabaseError as e:
            raise psycopg2.DatabaseError(messages.error_db_connection) from e

    def execute(self, query):
        '''
        Executes queries that make changes to the database - insert, update, etc
        :param query: the query to execute
        '''
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            self.conn.commit()
        except psycopg2.DatabaseError as e:
            raise psycopg2.DatabaseError(messages.error_db_query) from e

    def fetch(self, query):
        '''
        For fetching rows from the database only --> only select queries
        :param query: query to execute
        :return: fetched rows
        '''
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            return cur.fetchall()
        except psycopg2.DatabaseError as e:
            raise psycopg2.DatabaseError(messages.error_db_query) from e

    def disconnect(self):
        '''
        Closes the database connection
        '''
        try:
            self.conn.close()
        except psycopg2.DatabaseError as e:
            raise psycopg2.DatabaseError(messages.error_db_disconnection) from e
