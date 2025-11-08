import base64
import json
import os
import pymysql
from datetime import datetime

INSERT_CONFIG_SQL = """
    INSERT INTO config (name, value)
    VALUES (%s, %s)
"""

def create_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor
    )

def lambda_handler(event, context):
    # can be { "name": "...", "value": "..." } or [ {...}, {...} ]
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Invalid JSON body"}),
        }
    
    # only dicts allowed
    if not isinstance(body, dict):
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "error": "Body must be a JSON object of key: value pairs, e.g. {\"KEY\": \"value\"}"
                }
            ),
        }
    
    valid_items = {}
    invalid_items = []
    for name, value in body.items():
        if not isinstance(name, str) or not name.strip():
            invalid_items.append({name: value})
            continue

        if isinstance(value, str):
            value = value.strip()

        valid_items[name.strip()] = value

    if not valid_items and invalid_items:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "error": "No valid config keys in body",
                    "invalid": invalid_items,
                }
            ),
        }

    connection = None
    inserted = []
    updated = []

    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            names = list(valid_items.keys())
            format_strings = ",".join(["%s"] * len(names))
            
            # find existing
            cursor.execute(
                f"SELECT name FROM config WHERE name IN ({format_strings})",
                names,
            )
            existing_rows = cursor.fetchall()
            existing_names = {row["name"] for row in existing_rows}

            # update existing
            update_sql = "UPDATE config SET value = %s WHERE name = %s"
            for name in names:
                if name in existing_names:
                    cursor.execute(update_sql, (valid_items[name], name))
                    updated.append(name)

            # insert new
            insert_sql = "INSERT INTO config (name, value) VALUES (%s, %s)"
            for name in names:
                if name not in existing_names:
                    cursor.execute(insert_sql, (name, valid_items[name]))
                    inserted.append(name)

            connection.commit()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "Configs processed successfully",
                    "inserted": inserted,
                    "updated": updated,
                    "invalid": invalid_items,
                }
            ),
        }

    except Exception as e:
        if connection:
            connection.rollback()
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": f"Failed to process configs: {str(e)}"}),
        }
    finally:
        if connection:
            connection.close()
