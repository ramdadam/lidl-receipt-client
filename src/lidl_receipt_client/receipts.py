import json
import logging
from dataclasses import dataclass
from datetime import datetime
from os import path
from pathlib import Path
from typing import Optional

import jwt
import requests

from lidl_receipt_client.model import Receipt, Receipts

_LOG = logging.getLogger(__name__)


@dataclass
class AuthContext:
    access_token: str
    refresh_token: str


def refresh_auth(refresh_token: str) -> AuthContext:
    response = requests.post(
        "https://accounts.lidl.com/connect/token",
        data={"refresh_token": refresh_token, "grant_type": "refresh_token"},
        headers={
            "Authorization": "Basic TGlkbFBsdXNOYXRpdmVDbGllbnQ6c2VjcmV0",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    response_json = response.json()
    _LOG.debug("Requested new token")
    _LOG.debug(f"access token: {response_json['access_token']}")
    return AuthContext(
        access_token=response_json["access_token"],
        refresh_token=response_json["refresh_token"],
    )


def check_auth(refresh_token: str, access_token_str: str) -> AuthContext:
    if access_token_str:
        token = jwt.decode(access_token_str, options={"verify_signature": False})
        if datetime.fromtimestamp(token.get("exp")) > datetime.now():
            return AuthContext(
                access_token=access_token_str, refresh_token=refresh_token
            )
    return refresh_auth(refresh_token)


def request_ticket(
    existing_auth_context: AuthContext,
    work_dir: Path,
    receipt_id: str,
    country_code: str,
    language_code: str,
    prefer_cache: bool = True,
) -> (Optional[Receipt], AuthContext):
    ticket_cache_path = Path(path.join(work_dir, f"{receipt_id}.json"))
    if prefer_cache and Path.exists(ticket_cache_path):
        with open(ticket_cache_path) as f:
            _LOG.debug("reading from cache")
            return Receipt.from_json(json.load(f)), existing_auth_context
    auth_context = check_auth(
        existing_auth_context.refresh_token, existing_auth_context.access_token
    )
    ticket_raw_response = requests.get(
        f"https://tickets.lidlplus.com/api/v1/{country_code}/tickets/{receipt_id}",
        headers={
            "Accept-Language": language_code,
            "App": "com.lidl.eci.lidl.plus",
            "App-Version": "999.99.9",
            "Operating-System": "iOS",
            "Authorization": f"Bearer {auth_context.access_token}",
        },
    )
    if ticket_raw_response.status_code != 200:
        return None, auth_context
    receipt = Receipt.from_dict(ticket_raw_response.json())
    with open(ticket_cache_path, "w") as f:
        json.dump(receipt.to_json(), f)
    return receipt, auth_context


def request_tickets(
    existing_auth_context: AuthContext,
    page: int,
    language_code: str,
    country_code: str,
) -> (Receipts, AuthContext):
    auth_context = check_auth(
        existing_auth_context.refresh_token, existing_auth_context.access_token
    )
    ticket_raw_response = requests.get(
        f"https://tickets.lidlplus.com/api/v1/{country_code}/list/{page}",
        headers={
            "Accept-Language": language_code,
            "App": "com.lidl.eci.lidl.plus",
            "App-Version": "999.99.9",
            "Operating-System": "iOS",
            "Authorization": f"Bearer {auth_context.access_token}",
        },
    )
    if ticket_raw_response.status_code != 200:
        raise Exception("failed to retrieve receipts")
    receipts = Receipts.from_dict(ticket_raw_response.json())
    return receipts, auth_context


def get_receipts(
    language_code: str,
    country_code: str,
    access_token_str: str,
    refresh_token: str,
) -> (Receipts, AuthContext):
    auth_context = AuthContext(
        access_token=access_token_str, refresh_token=refresh_token
    )

    def request_paginated_tickets(requested_page: int, auth_context: AuthContext) -> Receipts:
        return request_tickets(
            auth_context, requested_page, language_code, country_code
        )

    first_page, auth_context = request_paginated_tickets(1, auth_context)
    all_pages = first_page

    if first_page.totalCount > 0:
        max_page = int(first_page.totalCount / first_page.size) + 1
        records_size = len(first_page.records)
        _LOG.info("fetching receipts")
        _LOG.info(f"page 1/{max_page} - total: {first_page.totalCount}")
        for page in range(2, max_page + 1):
            requested_receipts, auth_context = request_paginated_tickets(
                page, auth_context
            )
            all_pages.records += requested_receipts.records
            all_pages.page += 1
            records_size += len(requested_receipts.records)
            _LOG.info(
                f"page {page}/{max_page}: {records_size}/{all_pages.totalCount}"
            )
    _LOG.info(f"finished fetching all pages")
    return all_pages, auth_context
