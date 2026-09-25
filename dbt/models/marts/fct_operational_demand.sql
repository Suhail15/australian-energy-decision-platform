select
    region_id,
    interval_start_utc,
    interval_start_aest,
    interval_start_utc + interval '30 minutes' as interval_end_utc,
    cast(interval_start_aest as date) as local_date,
    operational_demand_mw,
    demand_adjustment_mw,
    source_file
from {{ ref('stg_operational_demand') }}
