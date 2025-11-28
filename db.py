import mysql.connector
from mysql.connector import pooling
import os

#  MySQL configuration — uses environment variables with safe defaults
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', 'Ganesh@20367'),   # your password
    'database': os.environ.get('DB_NAME', 'plant_disease_db'),
    'auth_plugin': 'mysql_native_password'
}

#  Create a connection pool (5 reusable connections)
cnxpool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    pool_reset_session=True,
    **DB_CONFIG
)

#  Function to get a connection from pool
def get_conn():
    return cnxpool.get_connection()
