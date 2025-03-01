#!/usr/bin/env python3

import psycopg2
import math
from datetime import datetime, timedelta

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "database"  # Replace with your database name
DB_USER = "user"      # Replace with your username
DB_PASSWORD = "password"  # Replace with your password

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS sinewave (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    value DOUBLE PRECISION NOT NULL
);
"""

INSERT_VALUES_QUERY = """
INSERT INTO sinewave (timestamp, value)
VALUES (%s, %s);
"""

def generate_sine_wave_values():
    """Generate 100 sine wave values with timestamps."""
    start_time = datetime.now()
    values = []

    for i in range(100):
        timestamp = start_time + timedelta(seconds=i)
        value = math.sin(math.radians(i * 360 / 100))  # Sine value in radians
        values.append((timestamp, value))

    return values

def create_and_populate_table():
    """Create the sinewave table and populate it with sine wave data."""
    try:
        # Connect to the database
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        connection.autocommit = True

        with connection.cursor() as cursor:
            # Create the sinewave table
            cursor.execute(CREATE_TABLE_QUERY)
            print("Table 'sinewave' created successfully (if it didn't already exist).")

            # Generate sine wave data
            sine_wave_values = generate_sine_wave_values()

            # Populate the table with sine wave data
            cursor.executemany(INSERT_VALUES_QUERY, sine_wave_values)
            print("Table 'sinewave' populated with 100 sine wave values.")

    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()

def main():
    create_and_populate_table()

if __name__ == "__main__":
    main()
