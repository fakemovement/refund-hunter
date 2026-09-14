"""State storage: one JSON document per user. Local file for dev, DynamoDB when deployed."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .config import settings
from .models import State


class Store:
    def load(self, user_id: str = "local") -> State:  # pragma: no cover - interface
        raise NotImplementedError

    def save(self, state: State) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def reset(self, user_id: str = "local") -> State:
        state = State(user_id=user_id)
        self.save(state)
        return state


class LocalStore(Store):
    def __init__(self, data_dir: Path | None = None):
        self.dir = Path(data_dir or settings.data_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: str) -> Path:
        return self.dir / f"state_{user_id}.json"

    def load(self, user_id: str = "local") -> State:
        p = self._path(user_id)
        if not p.exists():
            return State(user_id=user_id)
        return State.model_validate_json(p.read_text(encoding="utf-8"))

    def save(self, state: State) -> None:
        self._path(state.user_id).write_text(
            state.model_dump_json(indent=2), encoding="utf-8"
        )


class DynamoStore(Store):
    """Single table: PK=USER#<id>, SK=STATE. On-demand capacity."""

    def __init__(self, table_name: str | None = None, region: str | None = None):
        import boto3

        self.table_name = table_name or settings.ddb_table
        region = region or os.getenv("RH_AWS_REGION") or os.getenv("AWS_REGION") or "us-east-1"
        self._ddb = boto3.resource("dynamodb", region_name=region)
        self.table = self._ddb.Table(self.table_name)

    @classmethod
    def ensure_table(cls, table_name: str | None = None, region: str | None = None) -> str:
        import boto3

        name = table_name or settings.ddb_table
        client = boto3.client(
            "dynamodb", region_name=region or os.getenv("RH_AWS_REGION") or "us-east-1"
        )
        if name not in client.list_tables()["TableNames"]:
            client.create_table(
                TableName=name,
                BillingMode="PAY_PER_REQUEST",
                AttributeDefinitions=[
                    {"AttributeName": "PK", "AttributeType": "S"},
                    {"AttributeName": "SK", "AttributeType": "S"},
                ],
                KeySchema=[
                    {"AttributeName": "PK", "KeyType": "HASH"},
                    {"AttributeName": "SK", "KeyType": "RANGE"},
                ],
            )
            client.get_waiter("table_exists").wait(TableName=name)
        return name

    def load(self, user_id: str = "local") -> State:
        item = self.table.get_item(Key={"PK": f"USER#{user_id}", "SK": "STATE"}).get("Item")
        if not item:
            return State(user_id=user_id)
        return State.model_validate_json(item["json"])

    def save(self, state: State) -> None:
        self.table.put_item(
            Item={
                "PK": f"USER#{state.user_id}",
                "SK": "STATE",
                "json": state.model_dump_json(),
                "updated_at": state.updated_at.isoformat(),
            }
        )


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = DynamoStore() if settings.store == "dynamodb" else LocalStore()
    return _store


def dumps(obj) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)
