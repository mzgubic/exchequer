import os
import pandas as pd
import argparse
import mysql.connector
from mysql.connector import errorcode
import utils

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
            utils.add_csv(csv_path, cursor, 'expenses')

    else:
        utils.add_csv('expense_csvs/private_individual.csv', cursor, 'expenses')
        utils.add_csv('expense_csvs/repeated.csv', cursor, 'expenses')
        utils.add_csv('income_csvs/income.csv', cursor, 'incomes')
       

if __name__ == '__main__':
    main()

