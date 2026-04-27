select *
from {{ ref('stg_beacon_events') }}
where event_type in ('page_view', 'answer_submitted', 'question_skipped')
  and quiz_step = 'question'
  and display_order is null
