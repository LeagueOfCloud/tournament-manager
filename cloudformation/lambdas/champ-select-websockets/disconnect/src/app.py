import os
import boto3
from typing import Any, Dict

ddb_client = boto3.client("dynamodb")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    try:
        connection_id = event["requestContext"]["connectionId"]

        item = {
            "connectionId": {"S": connection_id}
        }
        
        print(item)

        delete_item(
            table_name=os.environ["TABLE_NAME"],
            item=item
        )

    except Exception as e:
        print("it broke" + str(e))
        return {"statusCode": 500}

    return {"statusCode": 200}


def delete_item(table_name: str, item: Dict[str, Any]) -> None:
    ddb_client.delete_item(
        TableName=table_name,
        Key=item
    )