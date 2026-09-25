select
    region_id,
    interval_start_utc,
    timezone('Australia/Brisbane', interval_start_utc) as interval_start_aest,
    cast(operational_demand_mw as double) as operational_demand_mw,
    cast(demand_adjustment_mw as double) as demand_adjustment_mw,
    source_file
from {{ source('aemo', 'raw_demand') }}
