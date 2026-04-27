select
  quiz_step,
  display_order,
  count(*) filter (where event_type = 'page_view') as view_count,
  count(*) filter (where event_type = 'answer_submitted') as answer_count,
  count(*) filter (where event_type = 'question_skipped') as skip_count,
  count(distinct session_id) as session_count
from {{ ref('fct_quiz_events') }}
where quiz_step is not null
group by 1, 2
order by display_order nulls first, quiz_step
