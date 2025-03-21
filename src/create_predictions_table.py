import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_HOST = "localhost"  # Or the IP address of the container host
DB_PORT = "5432"       # Default PostgreSQL port
DB_NAME = "database"  # Replace with your database name
DB_USER = "user"  # Replace with your username
DB_PASSWORD = "password"  # Replace with your password

# SQL command to create the users table
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    prediction_bitcoin DECIMAL(20, 8) NOT NULL,
    prediction_oil DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def main():
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        connection.autocommit = True

        # Create a cursor to execute SQL commands
        with connection.cursor() as cursor:
            # Execute the table creation query
            cursor.execute(CREATE_TABLE_QUERY)
            print("Table 'users' created successfully (if it didn't already exist).")

    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        # Close the connection
        if connection:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()