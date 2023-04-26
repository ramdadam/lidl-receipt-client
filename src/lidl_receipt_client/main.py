import logging
from _decimal import Decimal
from pathlib import Path

import click

from lidl_receipt_client.analyze import group_sum_by_article
from lidl_receipt_client.receipts import get_receipts, request_ticket

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)

@click.command()
@click.argument(
    "refresh-token",
    type=str,
)
@click.argument(
    "work-dir",
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.option(
    "--access-token",
    type=str,
    help="access token to prevent refresh if valid",
)
@click.option(
    "--country-code",
    type=str,
    default="DE",
    help="country code to fetch receipts from the LIDL stores in the selected country",
)
@click.option(
    "--language-code", type=str, default="DE", help="language code for localization"
)
@click.option(
    "--use-cache", type=bool, default=True, help="always fetch the receipt details"
)
def fetch_all_receipts(
        refresh_token: str,
        work_dir: Path,
        access_token: str,
        country_code: str,
        language_code: str,
        use_cache: bool,
):
    receipts, auth_context = get_receipts(
        language_code=language_code,
        country_code=country_code,
        access_token_str=access_token,
        refresh_token=refresh_token,
    )
    total_amount = 0
    for receipt_summary in receipts.records:
        total_amount += Decimal(receipt_summary.totalAmount.replace(",", "."))
        receipt, auth_context = request_ticket(
            existing_auth_context=auth_context,
            work_dir=work_dir,
            receipt_id=receipt_summary.id,
            language_code=language_code,
            country_code=country_code,
            prefer_cache=use_cache,
        )
    _LOG.info(f"total: {total_amount}")


@click.command()
@click.argument(
    "receipts-path",
    type=click.Path(file_okay=False, dir_okay=True),
)
def analyze_receipts(receipts_path: Path):
    group_sum_by_article(receipts_path)
