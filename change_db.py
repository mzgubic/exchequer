import pandas as pd
import argparse
import mysql.connector
from mysql.connector import errorcode
import utils

def in_db(row, cursor):

    # add conditions
    conditions = []
    for key in row.index:
        value = row.loc[key]
        if type(value) == str:
            conditions.append("{}='{}'".format(key, value.strip()))
        else:
            conditions.append("{}={}".format(key, value))
            
    # execute SQL query and record the results
    condition = '({})'.format(' AND '.join(conditions))
    query = 'SELECT EXISTS(SELECT * FROM expenses WHERE {})'.format(condition)
    cursor.execute(query)
    return bool(cursor.fetchall()[0][0])

def add_to_db(row, cursor):

    # build the query
    keys = list(row.index)
    values = list(row.values)
    values = ['\''+val.strip()+'\'' if type(val) == str else str(val) for val in values]
    query = 'INSERT INTO expenses ({}) VALUES ({})'.format(', '.join(keys), ', '.join(values))
    utils.print_table(cursor, 'expenses')

    # and execute it
    cursor.execute(query)

def check_df(df):

    columns = [c.strip() for c in df.columns]
    
    for key in utils.expenses_keys:
        if not key in columns:
            print('missing {} key'.format(key))
            exit(1)

def add_csv(csv_path, cursor):

    # extract the dataframe
    df = pd.read_csv(csv_path)
    check_df(df)

    # loop over the rows in the dataframe
    for i in df.index:

        # get row
        row = df.loc[i]

        # check if the item is not already in the database
        if not in_db(row, cursor):
            add_to_db(row, cursor)


def main():

    # parse arguments
    parser = argparse.ArgumentParser(description='change the database')
    parser.add_argument('--csv', type=str, nargs='+', default=[],
                        help='csv files from which to read the expenses')
    args = parser.parse_args()

    # connect
    cnx, cursor = utils.connect()
    cursor.execute('USE {}'.format(utils.db_name))

    # add entries via a csv file
    if args.csv:
        for csv_path in args.csv:
            add_csv(csv_path, cursor)
    

if __name__ == '__main__':
    main()

