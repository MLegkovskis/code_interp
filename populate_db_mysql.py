import mysql.connector
import numpy as np
import time

# Configuration parameters for MySQL
config = {
    'user': 'root',
    'password': 'password',
    'host': 'db',
    'database': 'mydb',
    'raise_on_warnings': True
}

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
    while True:
        populate_db()
        time.sleep(5)
