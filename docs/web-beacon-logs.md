# 웹 비콘 로그와 액세스 로그 이해하기

이 문서는 메인 README의 4단계 “분석 요건에 맞춰 액세스 로그 추가하기”를 보조합니다. 목표는 **브라우저에서 발생한 사용자 행동이 어떻게 raw 로그가 되고, 그 로그가 access/funnel 분석용 데이터로 확장되는지** 이해하는 것입니다.

## 한 줄 정의

웹 비콘 로그는 브라우저에서 발생한 사용자 행동을 작은 이벤트 payload로 만들어 서버에 전송하고, 서버가 그 이벤트를 분석 가능한 원본 로그로 저장한 것입니다.

이 실습에서는 다음 흐름으로 동작합니다.

```text
사용자 행동
  └─ app/static/beacon.js
      └─ POST /beacon
          └─ app/app.py
              └─ data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl
```

## 왜 “비콘”이라고 부르나?

비콘(beacon)은 “신호를 보낸다”는 뜻에 가깝습니다. 웹에서는 사용자가 페이지를 보거나 버튼을 누르는 순간 브라우저가 작은 신호를 서버로 보내는 패턴을 말합니다.

현대 웹에서는 보통 다음 방식 중 하나를 사용합니다.

- `navigator.sendBeacon(...)`
- `fetch(..., { keepalive: true })`
- 분석 SDK 또는 이벤트 수집 SDK
- 직접 만든 `/events`, `/track`, `/beacon` API

이 실습은 `navigator.sendBeacon`을 우선 사용하고, 지원되지 않을 때 `fetch` fallback을 사용합니다.

## 이 실습에서 수집하는 이벤트

| 이벤트 타입 | 언제 발생하나 | 왜 필요한가 |
| --- | --- | --- |
| `page_view` | landing, question, finish 화면이 표시될 때 | 사용자가 어디까지 접근했고 어떤 문제를 실제로 봤는지 알기 위해 |
| `answer_submitted` | 사용자가 답안을 제출할 때 | 정답/오답 행동을 분석하기 위해 |
| `question_skipped` | 사용자가 문제를 건너뛸 때 | 어느 문제에서 이탈 또는 스킵이 많은지 보기 위해 |

`page_view`는 이 실습에서 **접속/노출 access log** 역할을 합니다. 단순히 “웹 페이지 URL을 봤다”가 아니라 퀴즈 흐름의 어느 단계인지 함께 남깁니다.

## 어떤 로그가 어느 포인트에서 생성되나?

이 실습에서 “쌓이는 로그”라고 부르는 원본은 `events.jsonl`입니다. 브라우저는 먼저 이벤트 payload를 만들고, Flask 서버가 그 payload를 받아 JSONL 파일에 append합니다. 이후 MinIO, DuckDB, dbt는 그 원본 로그를 복사하거나 변환한 결과입니다.

| 단계 | 생성/처리 포인트 | 생기는 것 | 저장 위치 | 설명 |
| --- | --- | --- | --- | --- |
| 1 | 페이지 로드 후 `beacon.js` 초기화 | `page_view` payload | 아직 영구 저장 아님 | landing 화면 진입을 `quiz_step='landing'`으로 보냅니다. |
| 2 | 사용자가 `문제 풀기` 클릭 | `page_view` payload | 아직 영구 저장 아님 | 첫 문제가 화면에 표시되며 `quiz_step='question'`, `display_order=1`을 보냅니다. |
| 3 | 사용자가 `다음 문제` 클릭 | `page_view` payload | 아직 영구 저장 아님 | 다음 문제가 표시될 때마다 `display_order=2`, `display_order=3`처럼 증가합니다. |
| 4 | 사용자가 답안을 고르고 `답 제출` 클릭 | `answer_submitted` payload | 아직 영구 저장 아님 | `/api/answer`가 정답 여부를 계산한 뒤 `is_correct`, `quiz_step='question'`, `display_order`를 보냅니다. |
| 5 | 사용자가 `문제 패스` 클릭 | `question_skipped` payload | 아직 영구 저장 아님 | `/api/skip` 호출 후 `skip_reason='next_question'`, `quiz_step='question'`, `display_order`를 보냅니다. |
| 6 | 마지막 문제 후 finish 화면 표시 | `page_view` payload | 아직 영구 저장 아님 | 완료 화면 진입을 `quiz_step='finish'`로 보냅니다. |
| 7 | Flask `POST /beacon` | raw beacon log row | `data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl` | 이때부터 실제 로그 파일에 쌓입니다. 서버가 `received_at_server`, `server_metadata`도 추가합니다. |
| 8 | `scripts/upload_logs_to_minio.py` | raw object | `s3://raw/beacon-events/dt=YYYY-MM-DD/events.jsonl` | 로컬 JSONL 파일을 MinIO object storage로 복사합니다. |
| 9 | `scripts/load_minio_to_duckdb.py` | DuckDB raw table row | `warehouse/quiz.duckdb`의 `raw_beacon_events` | MinIO의 JSONL을 SQL로 조회 가능한 테이블에 적재합니다. |
| 10 | `dbt run` | staging/fact/mart 모델 | `stg_beacon_events`, `fct_quiz_events`, `mart_*` | raw 로그를 분석하기 쉬운 형태로 변환한 파생 데이터입니다. |
| 11 | `scripts/render_report.py` | HTML 리포트 | `reports/quiz_pipeline_report.html` | mart 결과를 사람이 볼 수 있는 간단한 시각화로 바꿉니다. |

주의할 점: `app/data/quiz.sqlite3`의 `questions` 테이블은 제품 데이터(seed data)이지 행동 로그가 아닙니다. 행동 로그는 `/beacon`을 통해 쌓이는 `events.jsonl`입니다.

## 이벤트 payload 예시

`answer_submitted` 이벤트 한 건은 대략 다음처럼 생겼습니다.

```json
{
  "event_id": "bfe4d2a0-...",
  "event_type": "answer_submitted",
  "schema_version": "1.0.0",
  "session_id": "5fb3b7c6-...",
  "anonymous_user_id": "anon-6c70...",
  "occurred_at_client": "2026-04-27T12:00:00.000Z",
  "received_at_server": "2026-04-27T12:00:01Z",
  "page_url": "http://localhost:8000/",
  "user_agent": "Mozilla/5.0 ...",
  "question_id": 1,
  "quiz_step": "question",
  "display_order": 1,
  "selected_choice": "B",
  "correct_choice": "B",
  "is_correct": true
}
```

### 공통 필드

| 필드 | 의미 | 왜 필요한가 |
| --- | --- | --- |
| `event_id` | 이벤트 한 건의 고유 ID | 중복 제거, 재처리 추적 |
| `event_type` | 이벤트 이름 | 어떤 행동인지 구분 |
| `schema_version` | 이벤트 구조 버전 | payload 구조 변경 추적 |
| `session_id` | 브라우저 세션 ID | 한 방문 안에서 행동 흐름 분석 |
| `anonymous_user_id` | 익명 사용자 ID | 로그인 없이도 반복 방문/행동 묶기 |
| `occurred_at_client` | 브라우저에서 발생한 시각 | 사용자가 실제 행동한 시각 |
| `received_at_server` | 서버가 받은 시각 | 수집 지연/순서 문제 진단 |
| `page_url` | 행동이 발생한 페이지 | 화면 맥락 파악 |
| `user_agent` | 브라우저/기기 정보 | 환경별 문제 진단 |

### 액세스/퍼널 분석 필드

| 필드 | 적용 이벤트 | 의미 | 규칙 |
| --- | --- | --- | --- |
| `quiz_step` | `page_view`, `answer_submitted`, `question_skipped` | 퀴즈 흐름 단계 | `landing`, `question`, `finish` 중 하나 |
| `display_order` | question-scoped 이벤트 | 한 세션에서 몇 번째로 표시된 문제인지 | 문제 화면 이벤트는 1부터 시작, landing/finish는 null |

### 이벤트별 필드

| 이벤트 | 추가 필드 |
| --- | --- |
| `page_view` | `question_id`, `quiz_step`, `display_order`, `referrer` |
| `answer_submitted` | `question_id`, `quiz_step`, `display_order`, `selected_choice`, `correct_choice`, `is_correct` |
| `question_skipped` | `question_id`, `quiz_step`, `display_order`, `skip_reason` |

## deterministic sample sequence

`scripts/generate_sample_events.py --overwrite`는 학습/검증을 위해 아래 8건을 만듭니다.

| 순서 | event_type | quiz_step | display_order | 설명 |
| --- | --- | --- | --- | --- |
| 1 | `page_view` | `landing` | null | 메인 화면 접속 |
| 2 | `page_view` | `question` | 1 | 첫 문제 노출 |
| 3 | `answer_submitted` | `question` | 1 | 첫 문제 정답 제출 |
| 4 | `page_view` | `question` | 2 | 두 번째 문제 노출 |
| 5 | `answer_submitted` | `question` | 2 | 두 번째 문제 오답 제출 |
| 6 | `page_view` | `question` | 3 | 세 번째 문제 노출 |
| 7 | `question_skipped` | `question` | 3 | 세 번째 문제 패스 |
| 8 | `page_view` | `finish` | null | 완료 화면 |

## 클라이언트 코드에서 확인할 부분

파일: [`app/static/beacon.js`](../app/static/beacon.js)

| 함수 | 역할 |
| --- | --- |
| `baseEvent(eventType, questionId, metadata)` | 모든 이벤트에 공통 필드와 access-log metadata를 합칩니다. |
| `showQuestion(...)` | 현재 문제 하나만 화면에 표시하고 question-scoped `page_view`를 보냅니다. |
| `submitAnswer(...)` | 정답/오답 결과와 `quiz_step='question'`, `display_order`를 보냅니다. |
| `skipQuestion(...)` | 스킵 이벤트와 `display_order`를 보냅니다. |
| `showFinish(...)` | 완료 화면 `page_view`를 보냅니다. |

실습 중에는 다음 순서로 읽어보세요.

1. `schemaVersion`, `sessionId`, `anonymousUserId`가 어떻게 만들어지는지 확인합니다.
2. `baseEvent(...)`가 공통 필드를 어떻게 채우는지 확인합니다.
3. landing `page_view`가 초기화 시점에 어떻게 전송되는지 확인합니다.
4. `showQuestion(...)`에서 `display_order`가 어떻게 계산되는지 확인합니다.
5. `submitAnswer(...)`, `skipQuestion(...)`에서 같은 `display_order`를 재사용하는지 확인합니다.
6. `showFinish(...)`에서 `quiz_step='finish'`를 보내는지 확인합니다.

## 서버 코드에서 확인할 부분

파일: [`app/app.py`](../app/app.py)

| 함수/route | 역할 |
| --- | --- |
| `/beacon` | 브라우저가 보낸 이벤트를 받는 API endpoint |
| `validate_event(...)` | 필수 공통 필드와 이벤트 타입을 검증 |
| `spool_event(...)` | 이벤트를 JSONL 파일에 append |

서버는 `/beacon`에서 access-log semantics를 모두 강제하지 않습니다. 이 실습에서는 다음 계층이 의미 검증을 담당합니다.

- 샘플 데이터: `scripts/generate_sample_events.py`
- dbt tests: `dbt_quiz/models/schema.yml`, `dbt_quiz/tests/*.sql`
- 최종 검증: `scripts/verify_pipeline.py`

## 왜 JSONL로 저장하나?

JSONL은 한 줄에 JSON 객체 하나를 저장하는 형식입니다.

```jsonl
{"event_type":"page_view","event_id":"..."}
{"event_type":"answer_submitted","event_id":"..."}
{"event_type":"question_skipped","event_id":"..."}
```

장점:

- append하기 쉽습니다.
- 한 줄이 이벤트 한 건이라 스트리밍/배치 처리 모두에 어울립니다.
- 일부 줄이 깨져도 다른 줄을 읽을 수 있습니다.
- S3 같은 object storage에 날짜 partition으로 저장하기 쉽습니다.

단점:

- 스키마가 강제되지 않으므로 별도 검증이 필요합니다.
- 중복 이벤트, 늦게 도착한 이벤트, 잘못된 타입을 처리해야 합니다.
- 대용량 분석에서는 Parquet 같은 컬럼형 포맷으로 변환하는 경우가 많습니다.

## sendBeacon을 쓰는 이유

사용자가 페이지를 이동하거나 닫는 순간에도 로그를 최대한 보내고 싶을 때 `navigator.sendBeacon`이 유용합니다.

일반 `fetch` 요청은 페이지 이동 중 취소될 수 있습니다. 반면 `sendBeacon`은 브라우저가 백그라운드로 작은 데이터를 보내도록 설계되어 사용자 경험을 덜 방해합니다.

다만 다음 한계도 있습니다.

- 응답 본문을 세밀하게 처리하기 어렵습니다.
- 전송 성공을 100% 보장하지 않습니다.
- 큰 payload에는 적합하지 않습니다.
- 광고 차단기, 네트워크 상태, 브라우저 정책의 영향을 받을 수 있습니다.

그래서 중요한 서비스 이벤트는 서버 쪽 업무 처리 로그와 함께 대조하거나, retry 가능한 수집 구조를 따로 설계합니다.

## 현업에서는 어떻게 확장하나?

| 실습 구성 | 현업 확장 예시 | 이유 |
| --- | --- | --- |
| `/beacon` API | 이벤트 수집 API, Segment, Snowplow, RudderStack | 수집 표준화, SDK 관리 |
| JSONL local spool | Kafka, Kinesis, Pub/Sub, S3 raw prefix | 대용량/비동기/재처리 지원 |
| MinIO | Amazon S3, GCS, ADLS | 안정적인 object storage/data lake |
| DuckDB | BigQuery, Snowflake, Databricks, Redshift | 팀 단위/회사 단위 분석 workload 처리 |
| shell script | Airflow, Dagster, Prefect | 스케줄링, 재시도, 의존성 관리 |

## 개인정보와 윤리 주의

웹 비콘 로그는 사용자 행동을 남기는 기능이므로 개인정보와 사용자 신뢰를 반드시 고려해야 합니다.

- 이메일, 전화번호, 이름 같은 직접 식별자를 payload에 넣지 않습니다.
- IP, user agent, URL query string에도 개인정보가 섞일 수 있습니다.
- 수집 목적과 보존 기간을 명확히 합니다.
- 필요한 필드만 수집합니다.
- 법적/조직 정책에 맞춰 동의, opt-out, 삭제 요청 대응을 설계합니다.

이 실습에서는 로그인 사용자 정보 없이 `anonymous_user_id`만 사용합니다.

## 디버깅 체크리스트

1. 브라우저 개발자 도구 Network 탭에서 `/beacon` 요청이 보이는가?
2. `/beacon` 응답 status가 `202 Accepted`인가?
3. `data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl` 파일이 생겼는가?
4. JSONL 안에 `event_type`, `quiz_step`, `display_order`가 들어 있는가?
5. `scripts/upload_logs_to_minio.py` 실행 후 MinIO `raw/beacon-events/...` object가 생겼는가?
6. `scripts/load_minio_to_duckdb.py` 실행 후 DuckDB `raw_beacon_events`에 row가 들어갔는가?
7. `mart_access_log_funnel`에 `view_count`, `answer_count`, `skip_count`가 들어갔는가?

## 이 문서를 읽고 나면 설명할 수 있어야 하는 것

- 웹 비콘 로그가 무엇인지
- `page_view`, `answer_submitted`, `question_skipped`가 왜 필요한지
- `quiz_step`, `display_order`가 어떤 분석 질문에서 나온 필드인지
- 공통 필드와 이벤트별 필드를 왜 나누는지
- raw 로그를 JSONL로 먼저 저장하는 이유
- 현업에서 이 구조가 S3/Kafka/Warehouse/Orchestrator로 어떻게 확장되는지
