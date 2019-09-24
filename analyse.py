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
    df_c = pd.DataFrame(cursor.fetchall(), columns=['category', 'sum'])
    df_c = insert_missing_values(df_c)

    # the earliest and latest dates: get the indices (to limit the plot range only)
    spends = df_my['sum'] != 0
    earliest = min(spends[spends].index)
    latest = max(spends[spends].index)
    
    # stack them
    categories = [c for c in df_c.category]
    values = {c:df_myc.query('category == "{}"'.format(c))['sum'].values.astype(float) for c in categories}
    y = np.row_stack([values[c] for c in categories])
    y_stack = np.cumsum(y, axis=0)

    # utils
    months = {1:'Jan', 4:'Apr', 7:'Jul', 10:'Oct'}

    # stacked plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        ax.fill_between(range(len(df_my)), 0 if i==0 else y_stack[i-1, :], y_stack[i, :], label=c, alpha=0.7)
    ax.plot(range(len(df_my)), df_my['sum'], c='k', label='total')

    ax.set_title('Monthly spending ({}/month)'.format(currency))
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xticks(range(len(df_my)))
    ax.set_xticklabels(['{}\n{}'.format(df_my.loc[i].year, months[df_my.loc[i].month]) if df_my.loc[i].month in [1, 4, 7, 10] else '' for i in range(len(df_my))])
    ax.set_xlim(earliest, latest)
    ax.grid(linestyle=':', color='k', alpha=0.2)
    ax.legend(loc='center right')
    plt.savefig('figures/monthly_stacked_{}.pdf'.format(currency))

    # unstacked plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        ax.plot(range(len(df_my)), values[c], label=c, alpha=0.9)
    ax.set_title('Monthly spending ({}/month)'.format(currency))
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xticks(range(len(df_my)))
    ax.set_xticklabels(['{}\n{}'.format(df_my.loc[i].year, months[df_my.loc[i].month]) if df_my.loc[i].month in [1, 4, 7, 10] else '' for i in range(len(df_my))])
    ax.set_xlim(earliest, latest)
    ax.grid(linestyle=':', color='k', alpha=0.2)
    ax.legend(loc='center right')
    plt.savefig('figures/monthly_unstacked_{}.pdf'.format(currency))


def per_weekday_plots(cursor, currency):
 
    # total expenses per category and day of the week
    query = ('SELECT category, WEEKDAY(date) as dow, SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY category, dow '
             'ORDER BY dow ')
    cursor.execute(query)
    df_cd = pd.DataFrame(cursor.fetchall(), columns=['category', 'day', 'sum'])
    df_cd['sum'] = df_cd['sum'].astype(float)
    df_cd = insert_missing_values(df_cd)
    df_cd.sort_values(by=['day', 'category'], inplace=True)
    df_cd.reset_index(drop=True, inplace=True)

    # total expenses per day of the week 
    query = ('SELECT WEEKDAY(date) as dow, SUM(converted_amount) AS sum FROM expenses '
             'LEFT JOIN converted ON expenses.id = converted.id '
             'GROUP BY dow '
             'ORDER BY dow ')
    cursor.execute(query)
    df_d = pd.DataFrame(cursor.fetchall(), columns=['day', 'sum'])
    df_d['sum'] = df_d['sum'].astype(float)

    # expenses per category (descending order)
    query = ('SELECT category, sum(converted_amount) FROM expenses '
             'LEFT JOIN converted ON expenses.id = converted.id '
             'GROUP BY category '
             'ORDER BY SUM(converted_amount) DESC')
    cursor.execute(query)
    df_c = pd.DataFrame(cursor.fetchall(), columns=['category', 'sum'])
    df_c['sum'] = df_c['sum'].astype(float)
    df_c = insert_missing_values(df_c)

    # compute the histograms
    categories = [c for c in df_c.category]
    values = {c:df_cd.query('category == "{}"'.format(c))['sum'].values.astype(float) for c in categories}

    # spending range: normalise per day
    cursor.execute('SELECT MIN(date) FROM expenses')
    earliest = cursor.fetchall()[0][0]
    cursor.execute('SELECT MAX(date) FROM expenses')
    latest = cursor.fetchall()[0][0]
    nweeks = ((latest-earliest).days)/7
    values = {c:values[c]/nweeks for c in values}

    # compute the maximum spend of a category per day
    ymax = np.max([np.max(values[c]) for c in values])

    # plotting utilities
    total_width = 0.8
    n_categories = len(categories)
    width = total_width / n_categories
    mid_points = np.arange(7)

    # make a bar plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        dx = i*width + width/2. - total_width/2.
        ax.bar(mid_points + dx, values[c], label=c, align='center', width=width)
    for i, row in df_d.iterrows():
        ax.text(i, ymax*1.01, '{:2.2f}'.format(row['sum']/nweeks), horizontalalignment='center')
    ax.set_title('Spending per day of the week ({}\day)'.format(currency))
    ax.set_xticks(mid_points)
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.grid(linestyle=':', color='k', alpha=0.2)
    ax.legend(loc='center left')
    plt.savefig('figures/weekday_{}.pdf'.format(currency))


def main():

    # parse arguments
    parser = argparse.ArgumentParser(description='analyse the database')
    parser.add_argument('--currency', type=str, default='EUR',
                        help='currency in which to display the results')
    args = parser.parse_args()

    # delete all old pdfs
    os.system('rm figures/*.pdf')

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

