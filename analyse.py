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


def main():

    # connect
    cnx, cursor = utils.connect()
    cursor.execute('USE {}'.format(utils.db_name))

    # compute the average exchange rates
    cursor.execute('select AVG(value) from fx where from_cur=\'GBP\' and to_cur=\'EUR\'')
    avg_rate_GBP_to_EUR = cursor.fetchall()[0][0]
    print(avg_rate_GBP_to_EUR)

    # compute the converted spending amount
    try:
        cursor.execute('drop view converted')
    except mysql.connector.errors.ProgrammingError:
        print('cant delete converted')
    query = ('CREATE VIEW converted AS '
             'SELECT expenses.id, '
                    '(CASE WHEN currency=\'EUR\' THEN amount ELSE amount*IFNULL(value, {}) END) as converted_amount '
             'FROM expenses LEFT JOIN fx ON '
             'expenses.date=fx.date AND fx.from_cur=\'GBP\''.format(avg_rate_GBP_to_EUR))
    cursor.execute(query)

    # total expenses per month/year
    query = ('SELECT YEAR(date), MONTH(date), SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY YEAR(date), MONTH(date) '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'sum'])

    # expenses per month/year/category
    query = ('SELECT YEAR(date), MONTH(date), category, SUM(converted_amount) FROM expenses '
             'LEFT JOIN converted ON converted.id = expenses.id '
             'GROUP BY YEAR(date), MONTH(date), category '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df_cat = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'category', 'sum'])
    df_cat = insert_missing_values(df_cat)

    # expenses per category
    query = ('SELECT category, sum(converted_amount) FROM expenses '
             'LEFT JOIN converted ON expenses.id = converted.id '
             'GROUP BY category '
             'ORDER BY SUM(converted_amount) DESC')
    cursor.execute(query)
    df_total_category_spending = pd.DataFrame(cursor.fetchall(), columns=['category', 'sum'])
    print(df_total_category_spending)
    
    # do stuff
    categories = [c for c in df_total_category_spending.category]
    values = {}
    for c in categories:
        this_df = df_cat[df_cat.category==c]
        values[c] = this_df['sum'].values.astype(float)

    y = np.row_stack([values[c] for c in categories])
    y_stack = np.cumsum(y, axis=0)

    # plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        ax.fill_between(range(len(df)), 0 if i==0 else y_stack[i-1, :], y_stack[i, :], label=c, alpha=0.7)
    ax.plot(range(len(df)), df['sum'], c='k', label='total')


    # cosmetics
    ax.set_title('Monthly spending (EUR/month)')
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(['{}-{}'.format(df.loc[i].year, df.loc[i].month) if df.loc[i].month in [1, 4, 7, 10] else '' for i in range(len(df))])
    ax.legend(loc='upper left')

    plt.savefig('spending.pdf')


    

if __name__ == '__main__':
    main()

