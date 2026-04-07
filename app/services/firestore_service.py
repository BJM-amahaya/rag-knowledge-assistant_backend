import json
import logging
from decimal import Decimal
from typing import Optional, Any

import boto3
from app.config import settings

logger = logging.getLogger(__name__)


class FirestoreService:
    """タスクデータの保存サービス。

    DYNAMODB_TASKS_TABLE が設定されていれば DynamoDB を使い、
    未設定ならメモリ辞書にフォールバックする。
    """

    def __init__(self):
        self._dict: dict[str, dict[str, Any]] = {}  # フォールバック用
        self._table = None
        table_name = settings.DYNAMODB_TASKS_TABLE
        if table_name:
            dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
            self._table = dynamodb.Table(table_name)
            logger.info(f"DynamoDB テーブル '{table_name}' に接続しました")
        else:
            logger.info("DYNAMODB_TASKS_TABLE 未設定 → メモリ辞書を使用します")

    def save(self, task_id: str, data: dict[str, Any]) -> None:
        if self._table:
            item = {"taskId": task_id, **data}
            # DynamoDB は float 非対応なので Decimal に変換
            item = json.loads(json.dumps(item), parse_float=Decimal)
            self._table.put_item(Item=item)
        else:
            self._dict[task_id] = data

    def get(self, task_id: str) -> Optional[dict[str, Any]]:
        if self._table:
            response = self._table.get_item(Key={"taskId": task_id})
            return response.get("Item")
        return self._dict.get(task_id)

    def get_all(self) -> list[dict[str, Any]]:
        if self._table:
            response = self._table.scan()
            return response.get("Items", [])
        return list(self._dict.values())

    def delete(self, task_id: str) -> Optional[dict[str, Any]]:
        if self._table:
            response = self._table.delete_item(
                Key={"taskId": task_id},
                ReturnValues="ALL_OLD",
            )
            return response.get("Attributes")
        return self._dict.pop(task_id, None)


firestore_service = FirestoreService()
