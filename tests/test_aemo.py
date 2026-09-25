from datetime import datetime, timezone

from energy_platform.aemo import _local_start, _rows


def test_price_report_parser_selects_declared_fields():
    report = b'I,TRADING,PRICE,3,SETTLEMENTDATE,REGIONID,RRP,INVALIDFLAG,PRICE_STATUS\nD,TRADING,PRICE,3,"2026/08/05 00:05:00",QLD1,-50,0,FIRM\n'
    rows = list(_rows(report, "TRADING", "PRICE"))
    assert rows == [{"SETTLEMENTDATE": "2026/08/05 00:05:00", "REGIONID": "QLD1", "RRP": "-50", "INVALIDFLAG": "0", "PRICE_STATUS": "FIRM"}]


def test_end_timestamp_is_converted_to_local_interval_start():
    interval = _local_start("2026/08/05 00:00:00", 5)
    assert interval.isoformat() == "2026-08-04T23:55:00+10:00"
    assert interval.astimezone(timezone.utc) == datetime(2026, 8, 4, 13, 55, tzinfo=timezone.utc)
