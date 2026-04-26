select
  event_type,
  count(*) as cnt
from {{ ref('fct_quiz_events') }}
group by 1
order by 1
