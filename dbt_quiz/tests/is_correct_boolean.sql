select *
from {{ ref('stg_beacon_events') }}
where event_type = 'answer_submitted'
  and (is_correct is null or is_correct not in (true, false))
