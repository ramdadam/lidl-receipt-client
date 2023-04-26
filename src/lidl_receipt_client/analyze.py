import glob
import json
import logging
from _decimal import Decimal
from itertools import groupby
from operator import itemgetter, attrgetter
from os import path
from pathlib import Path
from typing import Tuple

from lidl_receipt_client.model import BoughtItem, Receipt

_LOG = logging.getLogger(__name__)


def serialize(work_dir: Path) -> list[BoughtItem]:
    serialized_items: list[BoughtItem] = []
    for receipt in glob.glob(path.join(work_dir, "*.json")):
        with open(receipt, "r") as f:
            receipt = Receipt.from_json(json.load(f))
            item: Receipt.ReceiptItem
            serialized_items += [
                BoughtItem.from_receipt(
                    item.currentUnitPrice,
                    item.quantity,
                    item.isWeight,
                    item.extendedAmount,
                    item.originalAmount,
                    item.description,
                    item.deposit,
                    receipt.storeCode,
                    receipt.date,
                )
                for item in receipt.itemsLine
            ]
    return serialized_items


def group_sum_by_article(receipts_path: Path):
    bought_items = serialize(receipts_path)

    bought_items.sort(key=attrgetter("description"))
    grouped_items: Tuple[str, list[BoughtItem]] = groupby(
        bought_items, attrgetter("description")
    )
    summed_items: list[Tuple[str, Decimal]] = []
    for key, data in grouped_items:
        data: list[BoughtItem]
        summ: Decimal = Decimal(0)
        for item in data:
            summ += item.total
        summed_items.append((key, summ))
    summed_items.sort(key=itemgetter(1))
    total_sum = 0
    for key, summ in summed_items:
        total_sum += summ
        _LOG.info(f"{key}: {summ}")
    _LOG.info(total_sum)
