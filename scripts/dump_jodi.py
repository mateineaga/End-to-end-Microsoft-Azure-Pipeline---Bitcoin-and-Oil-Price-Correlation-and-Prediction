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
    energy VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    value DOUBLE PRECISION,
    notes VARCHAR(255)
);
"""

INSERT_DATA_QUERY = """
INSERT INTO {table_name} (energy, code, country, date, value, notes)
VALUES (%s, %s, %s, %s, %s, %s);
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

def insert_data_from_csv(file_path, table_name, limit=10000):
    """Read data from a CSV file and insert up to a specified number of rows into the table."""
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

                row_count = 0
                for row in csv_reader:
                    if row_count >= limit:
                        break
                    energy, code, country, date, value, notes = row

                    # Convert `value` to None if it is empty or 'x'
                    value = None if value.strip() == "" or value.strip().lower() == "x" else float(value)

                    # Insert row into the table
                    cursor.execute(INSERT_DATA_QUERY.format(table_name=table_name),
                                   (energy, code, country, date, value, notes))
                    row_count += 1

            print(f"Inserted {row_count} rows from '{file_path}' into '{table_name}'.")
    except psycopg2.Error as e:
        print(f"Error inserting data: {e}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    finally:
        if connection:
            connection.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: ./insert_energy_data.py <csv_file_path> <table_name>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    table_name = sys.argv[2]

    # Create the table
    create_table(table_name)

    # Insert up to 10,000 rows from the CSV file
    insert_data_from_csv(csv_file_path, table_name, limit=10000)

if __name__ == "__main__":
    main()
