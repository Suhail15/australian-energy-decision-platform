select region_id, interval_start_utc
from {{ ref('fct_operational_demand') }}
group by 1, 2
having count(*) > 1
