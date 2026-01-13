import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    config = {
        'host': os.getenv('DB_HOST', '82.197.82.29'),
        'user': os.getenv('DB_USER', 'u659323332_robles'),
        'password': os.getenv('DB_PASSWORD', '+Ndn/&IH9'),
        'database': os.getenv('DB_NAME', 'u659323332_robles')
    }
    
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            
        return result
    except mysql.connector.Error as err:
        print(f"Database query error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

