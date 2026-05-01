import json
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from typing import Optional
from .config import settings

TABLE_NAME = "users"
OTP_TABLE_NAME = "pending_otps"


def _get_resource():
    return boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def get_table():
    return _get_resource().Table(TABLE_NAME)


def create_table_if_not_exists():
    dynamodb = _get_resource()
    existing = [t.name for t in dynamodb.tables.all()]
    if TABLE_NAME in existing:
        return dynamodb.Table(TABLE_NAME)

    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "email", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table


def get_user(email: str) -> Optional[dict]:
    table = get_table()
    response = table.get_item(Key={"email": email.lower()})
    return response.get("Item")


def create_otp_table_if_not_exists():
    dynamodb = _get_resource()
    existing = [t.name for t in dynamodb.tables.all()]
    if OTP_TABLE_NAME in existing:
        return dynamodb.Table(OTP_TABLE_NAME)

    table = dynamodb.create_table(
        TableName=OTP_TABLE_NAME,
        KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()

    # Enable TTL on the 'expires_at' attribute
    dynamodb.meta.client.update_time_to_live(
        TableName=OTP_TABLE_NAME,
        TimeToLiveSpecification={"Enabled": True, "AttributeName": "expires_at"},
    )
    return table


def get_otp_table():
    return _get_resource().Table(OTP_TABLE_NAME)


def store_pending_otp(email: str, hashed_otp: str, hashed_password: str, full_name: str, expires_at: int):
    table = get_otp_table()
    table.put_item(Item={
        "email": email.lower(),
        "hashed_otp": hashed_otp,
        "hashed_password": hashed_password,
        "full_name": full_name,
        "expires_at": expires_at,
    })


def get_pending_otp(email: str) -> Optional[dict]:
    table = get_otp_table()
    response = table.get_item(Key={"email": email.lower()})
    return response.get("Item")


def delete_pending_otp(email: str):
    table = get_otp_table()
    table.delete_item(Key={"email": email.lower()})


def create_user(email: str, hashed_password: str, full_name: str, created_at: str) -> dict:
    table = get_table()
    item = {
        "email": email.lower(),
        "hashed_password": hashed_password,
        "full_name": full_name,
        "created_at": created_at,
    }
    table.put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(email)",
    )
    return item


# ── Itinerary persistence ──────────────────────────────────────────────────────

ITINERARY_TABLE_NAME = "user_itineraries"


def get_itinerary_table():
    return _get_resource().Table(ITINERARY_TABLE_NAME)


def create_itinerary_table_if_not_exists():
    dynamodb = _get_resource()
    existing = [t.name for t in dynamodb.tables.all()]
    if ITINERARY_TABLE_NAME in existing:
        return dynamodb.Table(ITINERARY_TABLE_NAME)
    table = dynamodb.create_table(
        TableName=ITINERARY_TABLE_NAME,
        KeySchema=[
            {"AttributeName": "user_email", "KeyType": "HASH"},
            {"AttributeName": "itinerary_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_email", "AttributeType": "S"},
            {"AttributeName": "itinerary_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table


def upsert_itinerary(email: str, itinerary_id: str, data: dict) -> None:
    table = get_itinerary_table()
    table.put_item(Item={
        "user_email": email.lower(),
        "itinerary_id": itinerary_id,
        "data": json.dumps(data, default=str),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    })


def delete_itinerary_record(email: str, itinerary_id: str) -> None:
    table = get_itinerary_table()
    table.delete_item(Key={
        "user_email": email.lower(),
        "itinerary_id": itinerary_id,
    })


def list_itineraries(email: str) -> list[dict]:
    table = get_itinerary_table()
    response = table.query(KeyConditionExpression=Key("user_email").eq(email.lower()))
    items = []
    for item in response.get("Items", []):
        try:
            data = json.loads(item["data"])
            items.append({
                "itinerary_id": item["itinerary_id"],
                "destination": data.get("destination", ""),
                "start_date": data.get("startDate", ""),
                "end_date": data.get("endDate", ""),
                "num_days": data.get("numDays", 0),
                "saved_at": item.get("saved_at", ""),
            })
        except Exception:
            continue
    return items


def get_itinerary_data(email: str, itinerary_id: str) -> Optional[dict]:
    table = get_itinerary_table()
    response = table.get_item(Key={
        "user_email": email.lower(),
        "itinerary_id": itinerary_id,
    })
    item = response.get("Item")
    if not item:
        return None
    return json.loads(item["data"])
