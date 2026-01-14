import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': os.getenv('DB_HOST', '82.197.82.29'),
    'user': os.getenv('DB_USER', 'u659323332_robles'),
    'password': os.getenv('DB_PASSWORD', '+Ndn/&IH9'),
    'database': os.getenv('DB_NAME', 'u659323332_robles'),
    'autocommit': False
}

# Variable global para el pool
connection_pool = None

def init_connection_pool():
    """Inicializa el pool de conexiones una sola vez"""
    global connection_pool
    
    if connection_pool is not None:
        return connection_pool
    
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="hotel_robles_pool",
            pool_size=5,  # Máximo 5 conexiones reutilizables
            pool_reset_session=True,
            **db_config
        )
        print("✅ MySQL Connection Pool iniciado correctamente")
        return connection_pool
    except mysql.connector.Error as err:
        print(f"❌ Error al crear el connection pool: {err}")
        raise

def get_db_connection():
    """Obtiene una conexión del pool (en lugar de crear una nueva)"""
    global connection_pool
    
    if connection_pool is None:
        init_connection_pool()
    
    try:
        conn = connection_pool.get_connection()
        return conn
    except mysql.connector.Error as err:
        print(f"Error obteniendo conexión del pool: {err}")
        return None

def execute_query(query, params=None, fetch=False):
    """
    Ejecuta una query reutilizando conexiones del pool
    
    Args:
        query: SQL query a ejecutar
        params: Parámetros para la query
        fetch: Si True, retorna resultados. Si False, hace commit
    
    Returns:
        Resultados de la query o None si hay error
    """
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
        conn.rollback()
        return None
        
    finally:
        cursor.close()
        conn.close()  # Esto devuelve la conexión al pool, no la cierra realmente

# Inicializar el pool al importar el módulo
init_connection_pool()
