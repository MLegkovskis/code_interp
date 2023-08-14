import mysql.connector
import numpy as np
import time


# Configuration parameters for MySQL
config = {
    'user': 'root',
    'password': 'password',
    'host': 'db',
    'database': 'mydb',
    'port': '3306',
    'raise_on_warnings': True
}

def create_table():
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    time.sleep(5)
    create_table_query = """
    CREATE TABLE IF NOT EXISTS my_table (
        id INT AUTO_INCREMENT PRIMARY KEY,
        x1 FLOAT NOT NULL,
        x2 FLOAT NOT NULL,
        x3 FLOAT NOT NULL
    );
    """

    cursor.execute(create_table_query)
    cnx.commit()
    cursor.close()
    cnx.close()

def populate_db():
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    x1 = np.random.uniform(-np.pi, np.pi)
    x2 = np.random.uniform(-np.pi, np.pi)
    x3 = np.random.uniform(-np.pi, np.pi)

    cursor.execute("INSERT INTO my_table (x1, x2, x3) VALUES (%s, %s, %s)", (x1, x2, x3))
    cnx.commit()
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    create_table()
    while True:
        populate_db()
        time.sleep(2)
