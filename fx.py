import pandas as pd
import argparse
import mysql.connector
from mysql.connector import errorcode
import utils

def main():

    # parse arguments
    parser = argparse.ArgumentParser(description='add data to the fx table')
    parser.add_argument('--csv', type=str, default='fx_csvs/EUR_GBP.csv',
                        help='csv file from which to read the fx rates')
    parser.add_argument('--from', type=str, default='EUR',
                        help='rate from currency')
    parser.add_argument('--to', type=str, default='GBP',
                        help='rate to currency')
    args = parser.parse_args()

    # connect
    cnx, cursor = utils.connect()
    cursor.execute('USE {}'.format(utils.db_name))

    # add the 'from, to' information
    df = pd.read_csv(args.csv)
    df.columns=[c.strip() for c in df.columns]
    df['from_cur'] = getattr(args, 'from')
    df['to_cur'] = args.to
    df['date'] = pd.to_datetime(df.date, dayfirst=True).astype(str) # format correctly

    # add entries via a csv file
    utils.add_df(df, cursor, 'fx', precision=4)

    # add also the reverse exchange rate
    rev_df = df.copy()
    rev_df['from_cur'] = args.to
    rev_df['to_cur'] = getattr(args, 'from')
    rev_df['value'] = round(1./rev_df.value, 4)
    utils.add_df(rev_df, cursor, 'fx', precision=4)


if __name__ == '__main__':
    main()

