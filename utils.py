import mysql.connector
from mysql.connector import errorcode

db_name = 'exchequer'

expenses_keys = ['date', 'amount', 'currency', 'category', 'description']

def connect():

    # connect to the database
    cnx = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='mysqlpass',
    )

    cnx.autocommit = True

    # create a cursor object
    cursor = cnx.cursor()

    return cnx, cursor

def use_db(cursor):
    # use the existing database or create a new one
    try:
        cursor.execute('USE {}'.format(utils.db_name))
    except mysql.connector.Error as err:
        cursor.execute('CREATE DATABASE {}'.format(utils.db_name))

def tables(cursor):
    cursor.execute('SHOW TABLES')
    for (table, ) in cursor.fetchall():
        yield table

def print_table(cursor, table):
    cursor.execute('SELECT * FROM {}'.format(table))
    for row in cursor.fetchall():
        print(row)

