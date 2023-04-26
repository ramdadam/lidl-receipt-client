from _decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from dataclasses_json import dataclass_json
from dateutil import parser


@dataclass_json
@dataclass
class Receipts:
    @dataclass_json
    @dataclass
    class ReceiptSummary:
        id: str
        date: str
        totalAmount: str
        storeCode: str
        articlesCount: int
        couponsUsedCount: int
        hasReturnedItems: bool
        returnsCount: int
        returnedAmount: int
        invoiceRequestId: Optional[str]
        invoiceId: Optional[str]
        vendor: Optional[str]
        hasHtmlDocument: bool
        isHtml: bool

    page: int
    size: int
    totalCount: int
    records: List[ReceiptSummary]


@dataclass_json
@dataclass
class Receipt:
    @dataclass_json
    @dataclass
    class ReceiptItem:
        @dataclass_json
        @dataclass
        class Deposit:
            quantity: int
            taxGroup: str
            taxGroupName: str
            amount: str
            description: str
            unitPrice: str

        @dataclass_json
        @dataclass
        class Discount:
            description: str
            amount: str

        currentUnitPrice: str
        quantity: str
        isWeight: bool
        originalAmount: str
        extendedAmount: str
        description: str
        taxGroup: str
        taxGroupName: str
        codeInput: str
        discounts: list[Discount]
        deposit: Optional[Deposit]
        giftSerialNumber: Optional[str]

    itemsLine: list[ReceiptItem]
    date: str
    totalAmount: str
    storeCode: str


def eu_to_us_fp(price: str) -> Decimal:
    return Decimal(price.replace(",", "."))


@dataclass
class BoughtItem:
    @dataclass
    class Deposit:
        quantity: int
        unit_price: Decimal
        amount: Decimal
        description: str

        @staticmethod
        def from_deposit(deposit: Receipt.ReceiptItem.Deposit):
            return BoughtItem.Deposit(
                quantity=int(deposit.quantity),
                unit_price=eu_to_us_fp(deposit.unitPrice),
                amount=eu_to_us_fp(deposit.amount),
                description=deposit.description,
            )

    unit_price: Decimal
    quantity: Decimal
    is_weight: bool
    discount: Decimal
    total: Decimal
    description: str
    deposit: Optional[Deposit]
    store: str
    bought_time: datetime

    @staticmethod
    def from_receipt(
        unit_price: str,
        quantity: str,
        isWeight: bool,
        extendedAmount: str,
        originalAmount: str,
        description: str,
        deposit: Optional[Receipt.ReceiptItem.Deposit],
        store_code: str,
        date: str,
    ):
        extended_amount = eu_to_us_fp(extendedAmount)  # what you pay
        original_amount = eu_to_us_fp(
            originalAmount
        )  # what you would've paid without discount

        serialized_deposit = (
            None if deposit is None else BoughtItem.Deposit.from_deposit(deposit)
        )

        return BoughtItem(
            unit_price=eu_to_us_fp(unit_price),
            quantity=eu_to_us_fp(quantity),
            is_weight=isWeight,
            discount=original_amount - extended_amount,
            total=extended_amount,
            description=description,
            deposit=serialized_deposit,
            store=store_code,
            bought_time=parser.parse(date),
        )
