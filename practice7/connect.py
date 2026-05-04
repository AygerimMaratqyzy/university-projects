import psycopg2
from config import config

def connect():
    params = config()
    conn = psycopg2.connect(**params)
    return conn