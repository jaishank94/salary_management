from decimal import Decimal

from app.salary_stats import summarize_salaries


def test_empty_summary():
    summary = summarize_salaries([])
    assert summary.headcount == 0
    assert summary.minimum is None
    assert summary.average is None
    assert summary.median is None
    assert summary.total_payroll == Decimal("0.00")
    assert summary.bands == ()


def test_single_salary_is_every_statistic():
    summary = summarize_salaries([Decimal("10")])
    assert summary.minimum == summary.maximum == summary.average == summary.median == Decimal("10.00")
    assert summary.p25 == summary.p75 == Decimal("10.00")
    assert summary.bands[0].count == 1


def test_average_rounds_half_up_and_median_averages_the_two_middle_values():
    assert summarize_salaries([Decimal("1.00"), Decimal("1.01")]).average == Decimal("1.01")
    assert summarize_salaries([Decimal("1"), Decimal("2")]).median == Decimal("1.50")
    assert summarize_salaries([Decimal("10"), Decimal("20"), Decimal("30")]).median == Decimal("20.00")


def test_percentiles_use_nearest_rank():
    summary = summarize_salaries([Decimal(value) for value in (100, 200, 300, 400)])
    assert summary.minimum == Decimal("100.00")
    assert summary.maximum == Decimal("400.00")
    assert summary.average == Decimal("250.00")
    assert summary.median == Decimal("250.00")
    assert summary.p25 == Decimal("100.00")
    assert summary.p75 == Decimal("300.00")
    assert summary.total_payroll == Decimal("1000.00")
    assert sum(band.count for band in summary.bands) == 4


def test_equal_salaries_collapse_to_one_band():
    summary = summarize_salaries([Decimal("10"), Decimal("10"), Decimal("10")])
    assert len(summary.bands) == 1
    assert summary.bands[0].count == 3


def test_bands_include_every_salary():
    summary = summarize_salaries([Decimal(value) for value in (1, 2, 3, 4, 5)])
    assert sum(band.count for band in summary.bands) == 5
    assert summary.bands[0].minimum <= Decimal("1")
    assert summary.bands[-1].maximum >= Decimal("5")
