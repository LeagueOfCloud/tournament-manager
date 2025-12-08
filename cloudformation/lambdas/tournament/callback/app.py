import json
import os
import pymysql
import logging
import requests

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )

def lambda_handler(event, context):
    path_params = event.get("pathParameters") or {}
    
    try:
        connection = create_connection()       

    except Exception as e:
        return 