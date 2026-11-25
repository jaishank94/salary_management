"""Exact salary summaries.

SQLite's SUM/AVG use floating point. At this product's scale it is safer to
aggregate Decimal values in process than to publish a rounded float as pay.
"""

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from app.validation import as_decimal, quantize_money


@dataclass(frozen=True)
class SalaryBand:
    minimum: Decimal
    maximum: Decimal
    count: int


@dataclass(frozen=True)
class SalarySummary:
    headcount: int
    minimum: Decimal | None
    maximum: Decimal | None
    average: Decimal | None
    median: Decimal | None
    p25: Decimal | None
    p75: Decimal | None
    total_payroll: Decimal
    bands: tuple[SalaryBand, ...]


def _nearest_rank(ordered: list[Decimal], percent: int) -> Decimal:
    """Nearest-rank percentile. Rank 1 is the lowest salary."""
    rank = math.ceil(percent * len(ordered) / 100)
    rank = min(max(rank, 1), len(ordered))
    return ordered[rank - 1]


def _median(ordered: list[Decimal]) -> Decimal:
    count = len(ordered)
    midpoint = count // 2
    if count % 2 == 1:
        return ordered[midpoint]
    return quantize_money((ordered[midpoint - 1] + ordered[midpoint]) / Decimal(2))


def _bands(ordered: list[Decimal], buckets: int = 5) -> tuple[SalaryBand, ...]:
    low = ordered[0]
    high = ordered[-1]
    if low == high:
        return (SalaryBand(low, high, len(ordered)),)
    span = high - low
    usable = max(1, min(buckets, int(span / Decimal("0.01"))))
    if usable == 1:
        return (SalaryBand(low, high, len(ordered)),)
    width = span / Decimal(usable)
    counts = [0] * usable
    for value in ordered:
        if value >= high:
            index = usable - 1
        else:
            index = int(((value - low) / width).to_integral_value(rounding=ROUND_DOWN))
            index = min(max(index, 0), usable - 1)
        counts[index] += 1
    bands: list[SalaryBand] = []
    for index, count in enumerate(counts):
        start = low if index == 0 else low + width * index
        end = high if index == usable - 1 else low + width * (index + 1)
        bands.append(SalaryBand(quantize_money(start), quantize_money(end), count))
    return tuple(bands)


def summarize_salaries(salaries: list[object]) -> SalarySummary:
    ordered = sorted(quantize_money(as_decimal(amount)) for amount in salaries)
    if not ordered:
        return SalarySummary(0, None, None, None, None, None, None, Decimal("0.00"), ())
    total = quantize_money(sum(ordered, start=Decimal("0")))
    average = quantize_money(sum(ordered, start=Decimal("0")) / Decimal(len(ordered)))
    return SalarySummary(
        headcount=len(ordered),
        minimum=ordered[0],
        maximum=ordered[-1],
        average=average,
        median=_median(ordered),
        p25=_nearest_rank(ordered, 25),
        p75=_nearest_rank(ordered, 75),
        total_payroll=total,
        bands=_bands(ordered),
    )
