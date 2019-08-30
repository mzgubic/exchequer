import mysql.connector
from mysql.connector import errorcode
import utils

def main():

    # connect
    cnx, cursor = utils.connect()

    # use the existing database or create a new one
    try:
        cursor.execute('USE {}'.format(utils.db_name))
    except mysql.connector.Error as err:
        cursor.execute('CREATE DATABASE {}'.format(utils.db_name))

    # create a table if it doesn't exist
    table_defs = {}
    table_defs['expenses'] = ('CREATE TABLE expenses ('
                              'id INT NOT NULL AUTO_INCREMENT,'
                              'date DATE,'
                              'amount DECIMAL(10, 2) NOT NULL,'
                              'currency VARCHAR(3) NOT NULL,'
                              'category VARCHAR(20) NOT NULL,'
                              'description VARCHAR(255) NOT NULL,'
                              'PRIMARY KEY (id) )')

    for table_name in table_defs:
        if table_name not in utils.tables(cursor):
            cursor.execute(table_defs[table_name])

if __name__ == '__main__':
    main()

