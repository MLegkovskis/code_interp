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

def wait_for_db():
    retries = 5
    for _ in range(retries):
        try:
            cnx = mysql.connector.connect(**config)
            cnx.close()
            return
        except mysql.connector.Error:
            print("DB not ready. Waiting...")
            time.sleep(5)
    raise SystemExit("DB was not ready after multiple retries.")

def create_table():
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

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

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()

def populate_db(cursor, cnx):
    try:
        x1 = np.random.uniform(-np.pi, np.pi)
        x2 = np.random.uniform(-np.pi, np.pi)
        x3 = np.random.uniform(-np.pi, np.pi)
        cursor.execute("INSERT INTO my_table (x1, x2, x3) VALUES (%s, %s, %s)", (x1, x2, x3))
        cnx.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def main():
    create_table()

    # Open the connection
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    try:
        while True:
            populate_db(cursor, cnx)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    wait_for_db()
    main()
