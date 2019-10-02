import pandas as pd
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
        cursor.execute('USE {}'.format(db_name))
    except mysql.connector.Error as err:
        cursor.execute('CREATE DATABASE {}'.format(db_name))

def tables(cursor):
    cursor.execute('SHOW TABLES')
    for (table, ) in cursor.fetchall():
        yield table

def print_table(cursor, table):
    cursor.execute('SELECT * FROM {}'.format(table))
    for row in cursor.fetchall():
        print(row)


def in_table(row, cursor, table):

    # add conditions
    conditions = []
    for key in row.index:
        value = row.loc[key]
        if type(value) == str:
            conditions.append("{}='{}'".format(key, value.strip().replace("'", "''")))
        else:
            conditions.append("{}={}".format(key, value))
            
    # execute SQL query and record the results
    condition = '({})'.format(' AND '.join(conditions))
    query = 'SELECT EXISTS(SELECT * FROM {} WHERE {})'.format(table, condition)
    cursor.execute(query)
    return bool(cursor.fetchall()[0][0])

def add_to_table(row, cursor, table):

    # build the query
    keys = list(row.index)
    values = list(row.values)
    values = ['\''+val.strip().replace("'", "''")+'\'' if type(val) == str else str(val) for val in values]
    query = 'INSERT INTO {} ({}) VALUES ({})'.format(table, ', '.join(keys), ', '.join(values))

    # and execute it
    cursor.execute(query)

def check_df(df):

    columns = [c.strip() for c in df.columns]

    for key in expenses_keys:
        if not key in columns:
            print('missing {} key'.format(key))
            exit(1)

def add_csv(csv_path, cursor, table):

    # extract the dataframe
    df = pd.read_csv(csv_path)
    check_df(df)
    add_df(df, cursor, table)

def add_df(df, cursor, table):

    # loop over the rows in the dataframe
    for i in df.index:

        # get row
        row = df.loc[i]

        # check if the item is not already in the database
        if not in_table(row, cursor, table):
            print('Adding {}'.format(row))
            add_to_table(row, cursor, table)

