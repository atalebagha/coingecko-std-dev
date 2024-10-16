import os
import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal, Context
import math
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
price_table = dynamodb.Table(os.environ["PRICE_TABLE_NAME"])
stddev_table = dynamodb.Table(os.environ["STDDEV_TABLE_NAME"])


def calculate_stddev(prices):
    n = len(prices)
    if n < 2:
        return None
    mean = sum(prices) / n
    variance = sum((x - mean) ** 2 for x in prices) / (n - 1)
    return math.sqrt(variance)


def handler(event, context):
    try:
        for record in event["Records"]:
            if record["eventName"] == "INSERT":
                new_image = record["dynamodb"]["NewImage"]
                pair = new_image["pair"]["S"]
                time = int(new_image["time"]["N"])

                yesterday = time - 86400  # 24 hours in seconds

                # Query the price table for the specific coin's last 24 hours of data
                response = price_table.query(
                    KeyConditionExpression="pair = :pair AND #ts BETWEEN :yesterday AND :now",
                    ExpressionAttributeNames={"#ts": "time"},
                    ExpressionAttributeValues={
                        ":pair": pair,
                        ":yesterday": yesterday,
                        ":now": time,
                    },
                )

                prices = [Decimal(item["value"]) for item in response["Items"]]
                stddev = calculate_stddev(prices)

                ctx = Context(prec=38)

                safe_stddev = ctx.create_decimal_from_float(stddev)

                if stddev is not None:
                    stddev_table.put_item(
                        Item={"pair": pair, "stddev": safe_stddev, "updateBatch": time}
                    )

        return {
            "statusCode": 200,
            "body": json.dumps(f"Successfully calculated standard deviation"),
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
