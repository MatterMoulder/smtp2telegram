from __future__ import annotations

import base64
from dataclasses import dataclass

from zitadel_client import UserServiceListUsersRequest, UserServiceListQuery, UserServiceSearchQuery, \
    UserServiceEmailQuery, UserServiceTextQueryMethod, UserServiceListUserMetadataRequest
from zitadel_client.zitadel import Zitadel


@dataclass(frozen=True)
class ZitadelConfig:
    base_url: str
    pkay: str


class ZitadelClient:
    def __init__(self, config: ZitadelConfig) -> None:
        self.config = config
        self.client = Zitadel.with_private_key(config.base_url, config.pkay)

    def get_user_id_by_email(self, email: str) -> str:
        request = UserServiceListUsersRequest(
            query=UserServiceListQuery(limit=1, asc=True),
            queries=[
                UserServiceSearchQuery(
                    emailQuery=UserServiceEmailQuery(
                        emailAddress=email,
                        method=UserServiceTextQueryMethod.TEXT_QUERY_METHOD_EQUALS
                    )
                )
            ]
        )

        response = self.client.users.list_users(request)
        result = response.result or []
        return result[0].user_id if result else None

    def list_user_metadata(self, user_id: str) -> dict:
        request = UserServiceListUserMetadataRequest(user_id=user_id)
        response = self.client.users.list_user_metadata(request)
        return {
            m.key: base64.b64decode(m.value).decode()
            for m in (response.metadata or [])
        }

    def list_user_metadata_by_email(self, email: str) -> dict:
        user_id = self.get_user_id_by_email(email)
        if not user_id:
            return {}
        request = UserServiceListUserMetadataRequest(user_id=user_id)
        response = self.client.users.list_user_metadata(request)
        return {
            m.key: base64.b64decode(m.value).decode()
            for m in (response.metadata or [])
        }

    def get_telegram_id_from_metadata(self, user_id: str) -> str | None:
        metadata = self.list_user_metadata(user_id)
        return metadata.get("telegram.chat_id")


    def get_telegram_id_from_metadata_by_email(self, email: str) -> str | None:
        user_id = self.get_user_id_by_email(email)
        if not user_id:
            return None
        metadata = self.list_user_metadata(user_id)
        return metadata.get("telegram.chat_id")