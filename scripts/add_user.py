#!/usr/bin/env python3

import sys
import psycopg2
import hashlib

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "database"  # Replace with your database name
DB_USER = "user"      # Replace with your username
DB_PASSWORD = "password"  # Replace with your password

USAGE_MESSAGE = """
Usage: ./add_user.py <name> <email> <password>

Example:
    ./add_user.py "John Doe" "john.doe@example.com" "securepassword"
"""

def hash_password(password):
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(name, email, password_hash):
    """Insert a new user into the database."""
    insert_query = """
    INSERT INTO users (name, email, password_hash)
    VALUES (%s, %s, %s)
    """
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
            cursor.execute(insert_query, (name, email, password_hash))
            print("User added successfully.")
    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()

def main():
    if len(sys.argv) != 4:
        print("Error: Incorrect number of arguments.")
        print(USAGE_MESSAGE)
        sys.exit(1)

    name = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]

    # Hash the password
    password_hash = hash_password(password)

    # Add the user to the database
    add_user(name, email, password_hash)

if __name__ == "__main__":
    main()
