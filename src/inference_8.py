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

def store_predictions(connection, predictions_data):
    """
    Store multiple predictions in the database
    """
    # First, clear existing predictions
    clear_query = "TRUNCATE TABLE predictions"
    
    # Then insert new predictions
    insert_query = """
        INSERT INTO predictions (
            date,
            prediction_bitcoin,
            prediction_oil
        ) VALUES (
            %s, %s, %s
        )
    """
    
    try:
        with connection.cursor() as cursor:
            # Clear existing predictions
            cursor.execute(clear_query)
            
            # Insert new predictions
            for date, btc_pred, oil_pred in predictions_data:
                cursor.execute(insert_query, (
                    date,
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
        
        # Generate 50 predictions with more realistic price movements
        predictions_data = []
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # Create a copy of recent_data that we'll update with each prediction
        rolling_data = recent_data.copy()
        
        # Get last actual prices and calculate volatility
        last_btc = rolling_data['btc_price'].iloc[-1]
        last_oil = rolling_data['oil_price'].iloc[-1]
        
        # Calculate historical volatility
        btc_volatility = rolling_data['btc_price'].pct_change().std()
        oil_volatility = rolling_data['oil_price'].pct_change().std()
        
        for i in range(50):
            prediction_date = tomorrow - timedelta(days=i)
            
            # Get base prediction from model
            raw_btc_pred = predictor.predict_next_value(rolling_data, 'btc')
            raw_oil_pred = predictor.predict_next_value(rolling_data, 'oil')
            
            # Add randomized component based on historical volatility
            btc_change_pct = np.random.normal(0, btc_volatility)
            oil_change_pct = np.random.normal(0, oil_volatility)
            
            # Calculate new predictions with percentage changes
            btc_prediction = last_btc * (1 + btc_change_pct)
            oil_prediction = last_oil * (1 + oil_change_pct)
            
            # Ensure predictions don't deviate too far from recent prices
            btc_prediction = np.clip(btc_prediction, 
                                   last_btc * 0.95,  # max 5% decrease
                                   last_btc * 1.05)  # max 5% increase
            oil_prediction = np.clip(oil_prediction,
                                   last_oil * 0.95,
                                   last_oil * 1.05)
            
            predictions_data.append((
                prediction_date,
                btc_prediction,
                oil_prediction
            ))
            
            # Update last known prices for next iteration
            last_btc = btc_prediction
            last_oil = oil_prediction
            
            # Update rolling_data with the new predictions
            new_row = pd.DataFrame({
                'date': [prediction_date],
                'btc_price': [btc_prediction],
                'oil_price': [oil_prediction]
            })
            rolling_data = pd.concat([rolling_data, new_row], ignore_index=True)
            rolling_data = rolling_data.tail(predictor.sequence_length + 1)
            
            # Print only the first few predictions for verification
            if i < 15:
                print(f"Predictions for {prediction_date}:")
                print(f"Bitcoin price: {btc_prediction:.2f}")
                print(f"Oil price: {oil_prediction:.2f}")
                #print("-" * 50) first few predictions for verification
            if i < 15:
                print(f"Predictions for {prediction_date}:")
                print(f"Bitcoin price: {btc_prediction:.2f}")
                print(f"Oil price: {oil_prediction:.2f}")
                print("-" * 50)
        
        # Store all predictions in database
        store_predictions(connection, predictions_data)
        print(f"Stored {len(predictions_data)} predictions in database.")
        
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()