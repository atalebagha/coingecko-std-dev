import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STDDEV_TABLE_NAME"])
latest_update_table = dynamodb.Table(os.environ["LATEST_UPDATE_TABLE_NAME"])


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def get_latest_update_batch():
    response = latest_update_table.get_item(Key={"id": "latest_update"})
    return response["Item"]["time"] if "Item" in response else None


def get_all_coins(latest_batch, limit=100):
    response = table.query(
        IndexName="StdDevIndex",
        KeyConditionExpression=Key("updateBatch").eq(latest_batch),
        ScanIndexForward=False,  # This will sort in descending order
        Limit=limit,
    )

    return [
        {
            "pair": item["pair"],
            "stddev": float(item["stddev"]),
            "updateBatch": item["updateBatch"],
        }
        for item in response["Items"]
    ]


def get_specific_coin(pair, latest_batch):
    response = table.get_item(Key={"pair": pair})

    if "Item" not in response:
        return None

    item = response["Item"]
    if item["updateBatch"] != latest_batch:
        return None

    return {
        "pair": item["pair"],
        "stddev": float(item["stddev"]),
        "updateBatch": item["updateBatch"],
    }


def handler(event, context):
    try:
        latest_batch = get_latest_update_batch()
        if not latest_batch:
            return {
                "statusCode": 400,
                "body": json.dumps("No latest update data available"),
            }

        path_parameters = event.get("pathParameters", {})
        if path_parameters and "pair" in path_parameters:
            # Route for specific coin
            pair = path_parameters["pair"]
            coin_data = get_specific_coin(pair, latest_batch)
            if coin_data:
                response_data = coin_data
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps(f"No data found for coin pair: {pair}"),
                }
        else:
            # Route for all coins
            limit = int(event.get("queryStringParameters", {}).get("limit", 100))
            response_data = get_all_coins(latest_batch, limit)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(response_data, cls=DecimalEncoder),
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
