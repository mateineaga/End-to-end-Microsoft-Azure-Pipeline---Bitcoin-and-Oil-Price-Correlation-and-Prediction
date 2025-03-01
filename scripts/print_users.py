#!/usr/bin/env python3

import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "database"  # Replace with your database name
DB_USER = "user"      # Replace with your username
DB_PASSWORD = "password"  # Replace with your password

def print_users():
    """Fetch and print all records from the users table."""
    select_query = "SELECT * FROM users"
    try:
        # Connect to the database
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        with connection.cursor() as cursor:
            cursor.execute(select_query)
            rows = cursor.fetchall()
            if not rows:
                print("The users table is empty.")
                return

            # Print the rows
            print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Password Hash':<64}")
            print("-" * 120)
            for row in rows:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<30} {row[3]:<64}")

    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()

def main():
    print_users()

if __name__ == "__main__":
    main()
