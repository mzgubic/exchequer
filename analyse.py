import os
import numpy as np
import argparse
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import errorcode
import utils

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def insert_missing_values(df):
    """
    Fills zeros where no entries are found
    """

    # fill in all the categories
    categories = np.unique(df.category.values)

    for i in range(len(df)):
        year, month = df.loc[i].year, df.loc[i].month

        for c in categories:
            mask = np.logical_and(df.year == year, df.month == month)
            mask = np.logical_and(mask, df.category == c)
            
            if df[mask].empty:
                df = df.append({'year':year, 'month':month, 'category':c, 'sum':0}, ignore_index=True)

    df.sort_values(by=['year', 'month'], inplace=True)

    return df


def get_avg_fx(from_cur, to_cur, cursor):

    cursor.execute('SELECT AVG(value) FROM fx WHERE from_cur=\'{}\' AND to_cur=\'{}\''.format(from_cur, to_cur))
    avg = cursor.fetchall()[0][0]
    
    return avg


def get_currencies(cursor):

    query = 'SELECT DISTINCT currency FROM expenses'
    cursor.execute(query)
    currencies = [c[0] for c in cursor.fetchall()]
    return currencies


def compute_converted(cursor, currency):

    # get a list of all currencies
    currencies = get_currencies(cursor)
    foreign_cs = [c for c in currencies if not c==currency]

    # compute the average exchange rates
    avg_rates = {c:get_avg_fx(from_cur=c, to_cur=currency, cursor=cursor) for c in foreign_cs}

    try:
        cursor.execute('drop view converted')
    except mysql.connector.errors.ProgrammingError:
        print('cant delete converted')

    # build the query
    whens = ['WHEN currency=\'{}\' THEN amount*IFNULL(value, {})'.format(c, avg_rates[c]) for c in foreign_cs]
    query = 'CREATE VIEW converted AS ' + \
            'SELECT expenses.id, ' + \
                   '(CASE WHEN currency=\'{}\' THEN amount {} ELSE amount END) AS converted_amount '.format(currency, ' '.join(whens)) + \
            'FROM expenses LEFT JOIN fx ON ' + \
            'expenses.date=fx.date AND expenses.currency=fx.from_cur AND fx.to_cur=\'{}\''.format(currency)
    cursor.execute(query)


def per_month_plots(cursor, currency):

    # compute the converted spending amount
    compute_converted(cursor, currency)

    # total expenses per month/year
    query = ('SELECT YEAR(date), MONTH(date), SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY YEAR(date), MONTH(date) '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df_my = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'sum'])

    # expenses per month/year/category
    query = ('SELECT YEAR(date), MONTH(date), category, SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY YEAR(date), MONTH(date), category '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df_myc = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'category', 'sum'])
    df_myc = insert_missing_values(df_myc)

    # expenses per category (descending order)
    query = ('SELECT category, sum(converted_amount) FROM expenses '
             'LEFT JOIN converted ON expenses.id = converted.id '
             'GROUP BY category '
             'ORDER BY SUM(converted_amount) DESC')
    cursor.execute(query)
    df_cat = pd.DataFrame(cursor.fetchall(), columns=['category', 'sum'])
    
    # stack them
    categories = [c for c in df_cat.category]
    values = {c:df_myc.query('category == "{}"'.format(c))['sum'].values.astype(float) for c in categories}
    y = np.row_stack([values[c] for c in categories])
    y_stack = np.cumsum(y, axis=0)

    # stacked plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        ax.fill_between(range(len(df_my)), 0 if i==0 else y_stack[i-1, :], y_stack[i, :], label=c, alpha=0.7)
    ax.plot(range(len(df_my)), df_my['sum'], c='k', label='total')

    ax.set_title('Monthly spending ({}/month)'.format(currency))
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xticks(range(len(df_my)))
    ax.set_xticklabels(['{}-{}'.format(df_my.loc[i].year, df_my.loc[i].month) if df_my.loc[i].month in [1, 4, 7, 10] else '' for i in range(len(df_my))])
    ax.grid(linestyle=':', color='k', alpha=0.2)
    ax.legend(loc='upper left')
    plt.savefig('spending_stacked_{}.pdf'.format(currency))

    # unstacked plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        ax.plot(range(len(df_my)), values[c], label=c, alpha=0.9)
    ax.set_title('Monthly spending ({}/month)'.format(currency))
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xticks(range(len(df_my)))
    ax.set_xticklabels(['{}-{}'.format(df_my.loc[i].year, df_my.loc[i].month) if df_my.loc[i].month in [1, 4, 7, 10] else '' for i in range(len(df_my))])
    ax.grid(linestyle=':', color='k', alpha=0.2)
    ax.legend(loc='upper left')
    plt.savefig('spending_unstacked_{}.pdf'.format(currency))


def per_weekday_plots(cursor, currency):
    pass


def main():

    # parse arguments
    parser = argparse.ArgumentParser(description='analyse the database')
    parser.add_argument('--currency', type=str, default='EUR',
                        help='currency in which to display the results')
    args = parser.parse_args()

    # connect
    cnx, cursor = utils.connect()
    cursor.execute('USE {}'.format(utils.db_name))

    # per month plot
    per_month_plots(cursor, args.currency)

    # per weekday plot
    per_weekday_plots(cursor, args.currency)

    

if __name__ == '__main__':
    main()

