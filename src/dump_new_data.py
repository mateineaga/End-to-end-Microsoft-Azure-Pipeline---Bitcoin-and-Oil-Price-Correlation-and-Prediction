#!/usr/bin/env python3

import psycopg2
import csv
import sys

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "database"  # Replace with your database name
DB_USER = "user"      # Replace with your username
DB_PASSWORD = "password"  # Replace with your password

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    value DOUBLE PRECISION NOT NULL
);
"""

INSERT_DATA_QUERY = """
INSERT INTO {table_name} (date, value)
VALUES (%s, %s);
"""


def create_table(table_name):
    """Create a table in the database."""
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_QUERY.format(table_name=table_name))
            print(f"Table '{table_name}' created successfully.")
    except psycopg2.Error as e:
        print(f"Error creating table: {e}")
    finally:
        if connection:
            connection.close()


def insert_data_from_csv(file_path, table_name):
    """Read data from a CSV file and insert it into the specified table."""
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        connection.autocommit = True

        with connection.cursor() as cursor:
            with open(file_path, mode='r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip the header row
                for row in csv_reader:
                    date, value = row
                    cursor.execute(INSERT_DATA_QUERY.format(
                        table_name=table_name), (date, float(value)))
            print(
                f"Data from '{file_path}' inserted successfully into '{table_name}'.")
    except psycopg2.Error as e:
        print(f"Error inserting data: {e}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    finally:
        if connection:
            connection.close()


def main():
    if len(sys.argv) != 3:
        print("Usage: ./insert_data.py <csv_file_path> <table_name>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    table_name = sys.argv[2]

    # Create the table
    # create_table(table_name)

    # Insert data from the CSV file
    insert_data_from_csv(csv_file_path, table_name)


if __name__ == "__main__":
    # main()
    print('inserting into BTC_DAILY...')
    insert_data_from_csv('../data/bitcoin_data.csv', 'btc_daily')

    print('inserting into OIL_DAILY...')
    insert_data_from_csv('../data/RWTCd.csv', 'oil_daily')

    print('data inserted into both tables.')
