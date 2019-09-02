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

    # total expenses
    query = ('SELECT YEAR(date), MONTH(date), SUM(amount) FROM expenses '
             'GROUP BY YEAR(date), MONTH(date) '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'sum'])
    print(df)

    # expenses by category
    query = ('SELECT YEAR(date), MONTH(date), category, SUM(amount) FROM expenses '
             'GROUP BY YEAR(date), MONTH(date), category '
             'ORDER BY YEAR(date), MONTH(date)')
    cursor.execute(query)
    df_cat = pd.DataFrame(cursor.fetchall(), columns=['year', 'month', 'category', 'sum'])
    df_cat = insert_missing_values(df_cat)
    print(df_cat)

    # do stuff
    categories = np.unique(df_cat.category.values)
    values = {}
    for c in categories:
        this_df = df_cat[df_cat.category==c]
        values[c] = this_df['sum'].values.astype(float)

    y = np.row_stack([values[c] for c in sorted(values)])
    y_stack = np.cumsum(y, axis=0)

    # plot
    fig, ax = plt.subplots()
    for i, c in enumerate(categories):
        ax.fill_between(range(len(df)), 0 if i==0 else y_stack[i-1, :], y_stack[i, :], label=c, alpha=0.7)
    ax.plot(range(len(df)), df['sum'], c='k', label='total')


    # cosmetics
    ax.set_title('Monthly spending')
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(['{}-{}'.format(df.loc[i].year, df.loc[i].month) if df.loc[i].month in [1, 4, 7, 10] else '' for i in range(len(df))])
    ax.legend(loc='upper left')

    plt.savefig('spending.pdf')


    

if __name__ == '__main__':
    main()

