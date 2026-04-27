# 이벤트 설계와 A/B 테스트 확장 메모

이 문서는 메인 실습 밖의 읽을거리입니다.  
README에서는 **필수 beacon 이벤트 3종을 안정적으로 수집하고 적재하는 것**까지만 다룹니다.  
여기서는 그 다음 단계로 넘어갈 때 고려할 설계 포인트를 정리합니다.

## 이 실습의 최소 이벤트 계약

공통 필드:

- `event_id`
- `event_type`
- `schema_version`
- `session_id`
- `anonymous_user_id`
- `occurred_at_client`
- `received_at_server`
- `page_url`
- `user_agent`

이벤트 타입:

- `page_view`
- `answer_submitted`
- `question_skipped`

액세스/퍼널 분석 필드:

- `quiz_step`: `landing`, `question`, `finish`
- `display_order`: question-scoped 이벤트의 1-based 문항 노출 순서

## 왜 최소 계약이 중요한가

초기 실습에서는 “필드를 많이 넣는 것”보다 “필수 필드가 빠지지 않게 하는 것”이 더 중요합니다.

예를 들어:

- `event_id`가 없으면 중복 제거가 어려워집니다.
- `session_id`가 없으면 세션 기준 행동 흐름을 보기 어렵습니다.
- `occurred_at_client`와 `received_at_server`가 모두 없으면 지연이나 순서 문제를 진단하기 어렵습니다.
- `schema_version`이 없으면 이벤트 구조 변경을 추적하기 어렵습니다.

## 이벤트를 설계할 때 추가로 생각할 질문

### 1. 누가 행동했는가?

- 익명 사용자 기준이면 `anonymous_user_id`로 충분한가?
- 나중에 로그인 사용자가 들어오면 `user_id`와 어떻게 공존시킬 것인가?

### 2. 언제 행동했는가?

- 클라이언트 발생 시각과 서버 수신 시각을 둘 다 남길 것인가?
- 브라우저 시간 오차를 어떻게 다룰 것인가?

### 3. 어떤 맥락에서 행동했는가?

- 어떤 문제(`question_id`)에서 발생했는가?
- 퀴즈 흐름의 어느 단계(`quiz_step`)였는가?
- 몇 번째 문제 노출(`display_order`)에서 발생했는가?
- 어떤 화면/URL이었는가?
- 어떤 실험 variant에 속했는가?

## A/B 테스트로 확장하려면

이 실습은 A/B 테스트 분석을 본격적으로 다루지 않지만, 다음 필드를 추가하면 확장하기 쉬워집니다.

- `experiment_id`
- `variant_id`
- `assignment_reason`
- `assigned_at`

그리고 다음 원칙이 중요합니다.

1. **노출(exposure) 이벤트를 먼저 기록한다.**
2. **variant 할당 로직과 로그 기록 시점을 분리하지 않는다.**
3. **conversion 정의를 사후에 바꾸더라도 raw 로그는 최대한 보존한다.**

## 메트릭 설계 예시

퀴즈 앱에서 나중에 볼 수 있는 지표 예시:

- landing 접속 수
- 문제 노출 순서별 조회 수
- 문제 조회 수
- 정답 제출 수
- 오답 제출 수
- 문제별 스킵 수
- 세션당 평균 응답 수

하지만 이 실습의 메인 목표는 “좋은 지표를 설계하는 것”이 아니라,  
**그 지표를 만들 raw 데이터 공급망을 직접 구축해 보는 것**입니다.

## dbt 모델을 어떻게 확장할 수 있나

현재 계획은 다음 정도의 계층을 상정합니다.

- `stg_beacon_events`
- `fct_quiz_events`
- `mart_quiz_summary`
- `mart_access_log_funnel`

향후 확장 예시:

- `dim_questions`
- `mart_session_funnel`
- `mart_experiment_variant_summary`

이 확장은 README 메인 경로가 아니라 후속 학습 과제로 다루는 것이 적절합니다.

## 실무로 가져갈 때 꼭 확인할 것

- 이벤트 이름 규칙이 팀 전체에서 일관적인가?
- nullable 필드와 required 필드가 명확한가?
- schema versioning 전략이 있는가?
- duplicate / retry / late arrival 상황을 어떻게 처리할 것인가?
- raw 보존 정책과 개인정보 정책이 충돌하지 않는가?

핵심은, **메트릭은 바뀔 수 있어도 raw 이벤트는 다시 만들기 어렵다**는 점입니다.
