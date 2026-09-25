# Decision and acceptance criteria

The intended reader is a hypothetical small-business owner or analyst in Queensland considering whether a schedulable activity merits further investigation. The interface must show the schedule, amount of electricity moved, valid data coverage, distribution of daily outcomes, and the worst observed day. The report must explain that a real decision requires the business's interval meter data, tariff or contract terms, operating constraints, and future-price uncertainty.

Acceptance criteria:

1. Downloaded sources are traceable to URL and checksum and can be reprocessed without duplicating records.
2. Each market metric has a stated unit, interval length, and source table.
3. A complete day has 288 unique five-minute price records; incomplete days are excluded from paired comparisons.
4. Both scenario schedules use equal energy and respect configured hours and power limits.
5. Negative prices and high spikes are retained if the source record is otherwise valid.
6. Hand-calculated scenario fixtures agree with code, including one outcome where shifting costs more.
7. API, dashboard, BI exports, and memo reconcile to the same prepared data and shared calculation.
8. The final memo states the observed result and limitations without claiming customer-bill savings.
