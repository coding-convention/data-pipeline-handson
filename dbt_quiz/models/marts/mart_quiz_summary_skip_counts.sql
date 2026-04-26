select
  question_id,
  count(*) as skip_count
from {{ ref('fct_quiz_events') }}
where event_type = 'question_skipped'
group by 1
order by 1
