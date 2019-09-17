import os
import numpy as np
import argparse
import itertools
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

    columns = df.columns.values
    groups = {c:np.unique(df[c]) for c in columns if c != 'sum'}

    # loop over all combinations of all groups other than 'sum'
    for tup in itertools.product(*groups.values()):

        # check if the combination of values has a non zero sum
        group = {g:tup[i] for i, g in enumerate(groups.keys())}
        masks = {g:(df[g]==group[g]).values for g in group}
        mask = np.all([*masks.values()], axis=0)
        exists = np.any(mask)

        # and add a zero value if it doesnt
        if not exists:
            row = {g:group[g] for g in group}
            row['sum'] = 0
            df = df.append(row, ignore_index=True)

    return df


def get_avg_fx(from_cur, to_cur, cursor):

    cursor.execute('SELECT AVG(value) FROM fx WHERE from_cur=\'{}\' AND to_cur=\'{}\''.format(from_cur, to_cur))
    avg = cursor.fetchall()[0][0]

    if avg == None:
        print('WARNING: No conversion rate data from {f} to {t}. Using 1{f}=1{t}'.format(f=from_cur, t=to_cur))
        return 1.0
    else:
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
        cursor.execute('DROP VIEW converted')
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

    # total expenses per month/year
    query = ('SELECT YEAR(date), MONTH(date), SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY YEAR(date), MONTH(date) '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df_my = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'sum'])
    df_my = insert_missing_values(df_my)
    df_my.sort_values(by=['year', 'month'], inplace=True)
    df_my.reset_index(drop=True, inplace=True)

    # expenses per month/year/category
    query = ('SELECT YEAR(date), MONTH(date), category, SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY YEAR(date), MONTH(date), category '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df_myc = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'category', 'sum'])
    df_myc = insert_missing_values(df_myc)
    df_myc.sort_values(by=['year', 'month', 'category'], inplace=True)
    df_myc.reset_index(drop=True, inplace=True)

    # expenses per category (descending order)
    query = ('SELECT category, sum(converted_amount) FROM expenses '
             'LEFT JOIN converted ON expenses.id = converted.id '
             'GROUP BY category '
             'ORDER BY SUM(converted_amount) DESC')
    cursor.execute(query)
    df_cat = pd.DataFrame(cursor.fetchall(), columns=['category', 'sum'])
    df_cat = insert_missing_values(df_cat)
    
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
    ax.set_xticklabels(['{}-{}'.format(df_my.loc[i].year, df_my.loc[i].month) if df_my.loc[i].month in [1, 7] else '' for i in range(len(df_my))])
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
 
    # total expenses per month/year
    query = ('SELECT category, DAYOFWEEK(date) as dow, SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY category, dow '
             'ORDER BY category ')
    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall(), columns=['category', 'day', 'amount'])
    #print(df)



def main():

    # parse arguments
    parser = argparse.ArgumentParser(description='analyse the database')
    parser.add_argument('--currency', type=str, default='EUR',
                        help='currency in which to display the results')
    args = parser.parse_args()

    # delete all old pdfs
    os.system('rm *.pdf')

    # connect
    cnx, cursor = utils.connect()
    cursor.execute('USE {}'.format(utils.db_name))

    # compute the converted spending amount
    compute_converted(cursor, args.currency)

    # per month plot
    per_month_plots(cursor, args.currency)

    # per weekday plot
    per_weekday_plots(cursor, args.currency)

    

if __name__ == '__main__':
    main()

