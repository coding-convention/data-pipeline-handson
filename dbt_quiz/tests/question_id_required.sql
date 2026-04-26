select *
from {{ ref('stg_beacon_events') }}
where event_type in ('answer_submitted', 'question_skipped')
  and question_id is null
