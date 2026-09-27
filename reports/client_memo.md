# Decision brief: a two-hour operating-window move

## The question

If a Queensland business could move a 5 kW, two-hour activity from **16:00–18:00** to **11:00–13:00**, would that have changed its historical wholesale-price exposure? I kept a 5 kW background load from 08:00–20:00, so both schedules use **70 kWh per day**. This is an invented example; no customer meter or tariff data was used.

## What the data says

In the reserved **14 June–12 September 2026** holdout, **75 of 91 days** had a complete set of AEMO prices marked `FIRM`. Across those 75 paired days, the earlier schedule had **$236.43** of calculated wholesale exposure versus **$291.74** for the original schedule: a **$55.31 (18.96%)** difference. It was lower on each included day. The median daily difference was $0.73 and the smallest was $0.18. An independent SQL calculation matched the Python result to the cent.

There is a coverage caveat. **Sixteen days** were excluded because at least one price was marked `NOT FIRM`. If I include those prices in a separately labelled, provisional sensitivity, the comparison covers all 91 days: **$291.49** alternative versus **$357.24** original, a **$65.75 (18.41%)** difference. These extra prices may have been revised; I would not mix them into the confirmed-price result. In the earlier development period, the alternative was lower on **97.3% of 150** complete firm-price days, with a worst daily result of **−$0.94**. That is a useful reminder that the direction is not guaranteed every day.

## What I would recommend

I would use this result to justify a **customer-specific feasibility check**, not to change an operating schedule yet. The next inputs are interval meter readings, the actual retail tariff or wholesale-linked contract, the activity's flexibility, and any cost of moving it. A fixed retail tariff might pass none of this interval-by-interval wholesale difference through to the bill.

This is a retrospective comparison, not a forecast or a customer saving. It covers winter and early spring, retains negative prices and spikes, and excludes incomplete days from both schedules equally. The daily results and excluded dates are in [the holdout result](holdout_result.json) and [the provisional sensitivity](holdout_sensitivity.json).

Sources: [AEMO NEMWeb reports](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/market-management-system-mms-data/dispatch), [AEMO price-status procedure](https://www.aemo.com.au/-/media/Files/Electricity/NEM/5MS/Procedures-Workstream/Stakeholder-Consultation/Dispatch-Procedures/SO_OP_3705---Dispatch---clean.pdf), [AER retail-bill components](https://www.aer.gov.au/system/files/2025-08/State%20of%20the%20energy%20market%202025%20-%20Chapter%206%20-%20Retail%20energy%20markets%20and%20energy%20consumers.pdf).
