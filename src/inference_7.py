import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2 import sql, Error

# Database table creation query
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    prediction_bitcoin DECIMAL(20, 8) NOT NULL,
    prediction_oil DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class CryptoOilPredictor:
    def __init__(self, model_path, sequence_length=5):
        """
        Initialize predictor with path to saved models
        """
        self.sequence_length = sequence_length
        self.models = self._load_models(model_path)
        
    def _load_models(self, model_path):
        """
        Load all three models from the specified directory
        """
        return {
            'btc': load_model(os.path.join(model_path, 'btc_model.keras')),
            'oil': load_model(os.path.join(model_path, 'oil_model.keras')),
            'correlation': load_model(os.path.join(model_path, 'correlation_model.keras'))
        }
    
    def prepare_sequence(self, data, columns):
        """
        Prepare a sequence of the last n values for prediction
        """
        if isinstance(columns, str):
            sequence = data[columns].values[-self.sequence_length:]
            return sequence.reshape(1, self.sequence_length, 1)
        else:
            sequence = data[columns].values[-self.sequence_length:]
            return sequence.reshape(1, self.sequence_length, len(columns))
    
    def predict_next_value(self, data, model_type='btc'):
        """
        Predict the next value using the specified model
        """
        if model_type == 'btc':
            sequence = self.prepare_sequence(data, 'btc_price')
            prediction = self.models['btc'].predict(sequence, verbose=0)
        elif model_type == 'oil':
            sequence = self.prepare_sequence(data, 'oil_price')
            prediction = self.models['oil'].predict(sequence, verbose=0)
        elif model_type == 'correlation':
            sequence = self.prepare_sequence(data, ['btc_price', 'oil_price'])
            prediction = self.models['correlation'].predict(sequence, verbose=0)
        else:
            raise ValueError("Invalid model type. Choose 'btc', 'oil', or 'correlation'")
            
        return prediction[0][0]

def get_db_connection():
    """
    Create and return a database connection
    """
    try:
        connection = psycopg2.connect(
            host='localhost',
            database='database',
            user='user',
            password='password'
        )
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL Database: {e}")
        raise

def get_recent_data(connection, days=5):
    """
    Get the last n days of data where both BTC and oil data exists
    """
    query = """
        SELECT 
            b.date,
            b.value as btc_price,
            o.value as oil_price
        FROM btc_daily b
        INNER JOIN oil_daily o ON DATE(b.date) = DATE(o.date)
        ORDER BY b.date DESC
        LIMIT %s
    """
    
    try:
        # Create DataFrame from PostgreSQL query
        df = pd.read_sql_query(
            query, 
            connection, 
            params=(days,)
        )
        
        # Sort by date ascending to maintain correct sequence
        df = df.sort_values('date')
        
        return df
        
    except Error as e:
        print(f"Error executing query: {e}")
        raise

def store_predictions(connection, pred_date, btc_pred, oil_pred):
    """
    Store predictions in the database
    """
    query = sql.SQL("""
        INSERT INTO predictions (
            date,
            prediction_bitcoin,
            prediction_oil
        ) VALUES (
            %s, %s, %s
        )
    """)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (
                pred_date,
                float(btc_pred),
                float(oil_pred)
            ))
        connection.commit()
    except Error as e:
        print(f"Error storing predictions: {e}")
        connection.rollback()
        raise

def main():
    # Model path
    model_path = './20250115_011459'
    
    connection = None
    try:
        # Get database connection
        connection = get_db_connection()
        
        # Create predictions table if it doesn't exist
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_QUERY)
        connection.commit()
        
        # Get recent data
        recent_data = get_recent_data(connection)
        
        if len(recent_data) < 5:
            raise ValueError("Not enough recent data available. Need at least 5 days of historical data.")
        
        # Initialize predictor
        predictor = CryptoOilPredictor(model_path)
        
        # Make predictions for tomorrow
        tomorrow = datetime.now().date() + timedelta(days=1)
        btc_prediction = predictor.predict_next_value(recent_data, 'btc')
        oil_prediction = predictor.predict_next_value(recent_data, 'oil')
        
        # Store predictions in database
        store_predictions(
            connection,
            tomorrow,
            btc_prediction,
            oil_prediction
        )
        
        print(f"Predictions for {tomorrow}:")
        print(f"Bitcoin price: {btc_prediction:.8f}")
        print(f"Oil price: {oil_prediction:.2f}")
        
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()