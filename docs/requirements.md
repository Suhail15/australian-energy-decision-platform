# What this project needed to answer

I designed the example for a Queensland small-business owner or analyst asking whether a schedulable activity is worth investigating. A useful result needs more than a headline dollar figure: it should show the hours and energy moved, how many days had usable data, the spread of daily outcomes, and the worst observed day. It also needs to say what is missing for a real decision: interval meter data, tariff or contract terms, operating constraints, and uncertainty about future prices.

I used these checks as the definition of done:

1. Downloaded sources are traceable to URL and checksum and can be reprocessed without duplicating records.
2. Each market metric has a stated unit, interval length, and source table.
3. A complete day has 288 unique five-minute price records; incomplete days are excluded from paired comparisons.
4. Both scenario schedules use equal energy and respect configured hours and power limits.
5. Negative prices and high spikes are retained if the source record is otherwise valid.
6. Hand-calculated scenario fixtures agree with code, including one outcome where shifting costs more.
7. API, dashboard, BI exports, and memo reconcile to the same prepared data and shared calculation.
8. The [decision brief](../reports/client_memo.md) states the observed result and limits without claiming customer-bill savings.
