select
  answer_outcome,
  count(*) as submissions
from {{ ref('fct_quiz_events') }}
where answer_outcome is not null
group by 1
order by 1
