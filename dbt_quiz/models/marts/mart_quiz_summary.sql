select
  'total_events' as metric_name,
  count(*)::bigint as metric_value
from {{ ref('fct_quiz_events') }}
union all
select
  'answer_submissions' as metric_name,
  count(*)::bigint as metric_value
from {{ ref('fct_quiz_events') }}
where event_type = 'answer_submitted'
union all
select
  'correct_answers' as metric_name,
  count(*)::bigint as metric_value
from {{ ref('fct_quiz_events') }}
where event_type = 'answer_submitted' and is_correct = true
union all
select
  'incorrect_answers' as metric_name,
  count(*)::bigint as metric_value
from {{ ref('fct_quiz_events') }}
where event_type = 'answer_submitted' and is_correct = false
union all
select
  'skipped_questions' as metric_name,
  count(*)::bigint as metric_value
from {{ ref('fct_quiz_events') }}
where event_type = 'question_skipped'
