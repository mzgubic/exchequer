import mysql.connector
from mysql.connector import errorcode


def tables(cursor):
    cursor.execute('SHOW TABLES')
    for (table, ) in cursor.fetchall():
        yield table


def main():

    # connect to the database
    cnx = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='mysqlpass',
    )
    
    # create a cursor object
    cursor = cnx.cursor()

    # use the existing database or create a new one
    db_name = 'exchequer'
    try:
        cursor.execute('USE {}'.format(db_name))
    except mysql.connector.Error as err:
        cursor.execute('CREATE DATABASE {}'.format(db_name))

    # create a table if it doesn't exist
    table_defs = {}
    table_defs['expenses'] = ('CREATE TABLE expenses ('
                              'id INT NOT NULL AUTO_INCREMENT,'
                              'date DATE,'
                              'amount FLOAT NOT NULL,'
                              'currency VARCHAR(3) NOT NULL,'
                              'category VARCHAR(20) NOT NULL,'
                              'description VARCHAR(255) NOT NULL,'
                              'PRIMARY KEY (id) )')

    for table_name in table_defs:
        if table_name not in tables(cursor):
            cursor.execute(table_defs[table_name])



if __name__ == '__main__':
    main()

