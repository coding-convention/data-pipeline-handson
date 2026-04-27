select
  event_id,
  event_type,
  schema_version,
  session_id,
  anonymous_user_id,
  occurred_at_client,
  received_at_server,
  page_url,
  user_agent,
  question_id,
  selected_choice,
  correct_choice,
  is_correct,
  case
    when event_type = 'answer_submitted' and is_correct = true then 'correct'
    when event_type = 'answer_submitted' and is_correct = false then 'incorrect'
    else null
  end as answer_outcome,
  skip_reason,
  referrer,
  quiz_step,
  display_order,
  source_object_key,
  loaded_at
from {{ ref('stg_beacon_events') }}
