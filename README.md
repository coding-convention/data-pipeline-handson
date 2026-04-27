# 데이터 파이프라인 실습: Beacon 로그로 배우는 Hands-on Lab

> 학습자가 명령을 복사/붙여넣기 하면서 **웹 행동 로그가 raw 로그, 데이터 레이크, DuckDB 웨어하우스, dbt 모델, HTML 리포트로 변하는 과정**을 직접 확인하는 실습입니다.

이 저장소는 “데이터 엔지니어링이 무엇인가?”를 설명으로만 이해하는 대신, 아주 작은 퀴즈 서비스를 통해 다음 청사진을 몸으로 익히게 합니다.

```text
사용자 행동
  → 웹 비콘 로그 수집
  → 원본 로그 보존
  → 데이터 레이크 업로드
  → 데이터 웨어하우스 적재
  → dbt 모델링/검증
  → 간단한 시각화 리포트
```

최종적으로는 자신의 프로젝트에서 “A/B 테스트, 퍼널, 답안 제출, 스킵 같은 유저 로그를 어떻게 남기고 데이터화할지”를 혼자 찾아갈 수 있는 정도를 목표로 합니다.

## 전체 학습 순서

1. [소개](#1-소개)
   - [1.1 왜 데이터 파이프라인이 필요한가?](#11-왜-데이터-파이프라인이-필요한가)
   - [1.2 데이터 보존 환경은 어떤 것이 있는지](#12-데이터-보존-환경은-어떤-것이-있는지)
2. [데이터 환경 구축 그리고 데이터 확인](#2-데이터-환경-구축-그리고-데이터-확인)
   - [2.1 환경 셋업](#21-환경-셋업)
   - [2.2 데이터를 확인하고 분석 해보기](#22-데이터를-확인하고-분석-해보기)
3. [데이터의 연계: DataLake → DWH](#3-데이터의-연계-datalake--dwh)
4. [분석 요건에 맞춰 액세스 로그 추가하기](#4-분석-요건에-맞춰-액세스-로그-추가하기)
5. [dbt로 분석 가능한 모델 만들기](#5-dbt로-분석-가능한-모델-만들기)
6. [최종 시각화와 검증](#6-최종-시각화와-검증)
7. [전체 재실행과 확장 읽기](#7-전체-재실행과-확장-읽기)

보조 읽을거리:

- [`docs/web-beacon-logs.md`](docs/web-beacon-logs.md): 웹 비콘 로그와 액세스 로그 설명
- [`docs/data-engineering-vs-analytics-engineering.md`](docs/data-engineering-vs-analytics-engineering.md): 데이터 엔지니어링과 분석 엔지니어링 경계
- [`docs/event-design-and-ab-testing.md`](docs/event-design-and-ab-testing.md): 이벤트 설계/A-B 테스트 확장
- [`docs/pipeline-architecture.md`](docs/pipeline-architecture.md): 아키텍처 변형안

---

## 1. 소개

### 1.1 왜 데이터 파이프라인이 필요한가?

**이 단계에서 배우는 것**

- 서비스 DB와 분석 로그는 목적이 다르다는 점
- raw 로그를 먼저 보존해야 나중에 재처리할 수 있다는 점
- “수집 → 보존 → 적재 → 모델링 → 시각화”가 데이터 파이프라인의 기본 골격이라는 점

퀴즈 웹 앱은 SQLite에 문제 3개를 저장합니다. 이것은 제품을 운영하기 위한 **애플리케이션 데이터**입니다. 하지만 사용자가 실제로 어떤 문제를 봤는지, 어떤 답을 냈는지, 어디서 패스했는지는 SQLite 문제 테이블만 봐서는 알 수 없습니다.

그래서 별도의 행동 로그가 필요합니다.

| 질문 | 필요한 로그/데이터 |
| --- | --- |
| 사용자가 퀴즈를 시작했는가? | `page_view` + `quiz_step='landing'` |
| 몇 번째로 어떤 문제가 노출됐는가? | `page_view` + `quiz_step='question'` + `display_order` |
| 정답/오답을 제출했는가? | `answer_submitted` + `is_correct` |
| 문제를 패스했는가? | `question_skipped` + `skip_reason` |
| 끝까지 도달했는가? | `page_view` + `quiz_step='finish'` |

이 실습의 핵심 흐름은 다음과 같습니다.

```text
브라우저 퀴즈 페이지
  └─ app/static/beacon.js
      └─ POST /beacon (Flask)
          ├─ SQLite: app/data/quiz.sqlite3
          └─ JSONL spool: data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl

Learner commands
  ├─ scripts/upload_logs_to_minio.py
  │   └─ s3://raw/beacon-events/dt=YYYY-MM-DD/events.jsonl
  ├─ scripts/load_minio_to_duckdb.py
  │   └─ warehouse/quiz.duckdb raw_beacon_events
  ├─ dbt run / dbt test
  │   └─ stg_beacon_events, fct_quiz_events, mart_*
  └─ scripts/render_report.py
      └─ reports/quiz_pipeline_report.html
```

### 1.2 데이터 보존 환경은 어떤 것이 있는지

**이 단계에서 배우는 것**

- 데이터를 “어디에 보존하는가”에 따라 목적과 읽는 사람이 달라진다는 점
- DataLake와 DWH가 같은 저장소 이름이 아니라 서로 다른 책임이라는 점
- 현업 도구가 달라도 계층 구조는 비슷하다는 점

| 계층 | 이 실습의 도구/경로 | 저장 목적 | 쓰기 주체 | 주로 읽는 사람/프로그램 | 현업 예시 |
| --- | --- | --- | --- | --- | --- |
| 애플리케이션 DB | `app/data/quiz.sqlite3` | 퀴즈 문제 3개 같은 제품 운영 데이터 | Flask 앱/시드 스크립트 | 웹 앱 | PostgreSQL, MySQL, Aurora/RDS, Cloud SQL |
| 로컬 raw landing | `data/raw_spool/beacon_events/.../events.jsonl` | 서버가 받은 이벤트 원본을 append-only로 임시 보존 | Flask `/beacon` | 업로드 스크립트, 디버거 | Kafka topic, Kinesis, Pub/Sub, log collector |
| DataLake raw zone | MinIO `raw/beacon-events/...` | 원본 로그를 오래 보존하고 재처리 가능하게 함 | `upload_logs_to_minio.py` | 적재 스크립트, 데이터 엔지니어 | Amazon S3, GCS, ADLS, 사내 S3-compatible storage |
| DWH/raw table | DuckDB `raw_beacon_events` | object storage의 raw 로그를 SQL로 조회 가능하게 함 | `load_minio_to_duckdb.py` | dbt, 분석 쿼리 | BigQuery, Snowflake, Redshift, Databricks, ClickHouse |
| 분석 모델 | dbt `stg_*`, `fct_*`, `mart_*` | raw 데이터를 재사용 가능한 분석 테이블로 정리 | dbt | 분석가, BI, 리포트 | dbt Cloud/Core, Dataform, SQLMesh |
| 시각화 | `reports/quiz_pipeline_report.html` | 지표를 사람이 보는 결과물로 표현 | `render_report.py` | 실습자/비즈니스 사용자 | Looker, Tableau, Power BI, Superset, Metabase |

### 기술스택 설명과 현업 대응표

| 영역 | 실습 도구 | 실습에서의 역할 | 현업에서 실제로 많이 쓰는 것 | 핵심 개념 |
| --- | --- | --- | --- | --- |
| 웹 애플리케이션 | Flask | 퀴즈 페이지, 답안 API, `/beacon` 수집 API | Spring Boot, FastAPI, Django, Rails, Express, Next.js API routes | 이벤트 발생지 |
| 제품 데이터 저장소 | SQLite | 퀴즈 문제 저장 | PostgreSQL, MySQL, DynamoDB | 운영 데이터/OLTP |
| 브라우저 이벤트 수집 | `navigator.sendBeacon`, `fetch keepalive` | 사용자 행동 payload 전송 | Segment, Snowplow, RudderStack, GA4, Amplitude, Mixpanel, 직접 만든 수집 API | event tracking |
| 데이터 레이크 | MinIO | S3 호환 raw bucket | S3, GCS, ADLS | raw 보존, partition, object key |
| 웨어하우스 | DuckDB | 로컬 SQL 분석 DB | BigQuery, Snowflake, Redshift, Databricks, ClickHouse | SQL 분석, batch load |
| 모델링 | dbt Core | staging/fact/mart와 테스트 | dbt Cloud/Core, Dataform, SQLMesh | 변환, lineage, 품질 테스트 |
| 오케스트레이션 | shell/Python scripts | 순서대로 파이프라인 실행 | Airflow, Dagster, Prefect, Argo, GitHub Actions | 의존성, 재실행, 실패 복구 |
| 데이터 품질 | dbt tests, `verify_pipeline.py` | 이벤트 계약/테이블/리포트 검증 | Great Expectations, Soda, Deequ, observability 도구 | “돌았다”가 아니라 “맞다” |
| BI/시각화 | 정적 HTML | 최종 지표 확인 | Looker, Tableau, Power BI, Superset, Metabase | 데이터 소비 지점 |

> 이 실습은 현업 플랫폼을 그대로 복제하지 않습니다. 대신 같은 책임을 작은 도구로 축소해서 학습합니다.

---

## 2. 데이터 환경 구축 그리고 데이터 확인

### 2.1 환경 셋업

**이 단계에서 배우는 것**

- Docker Compose로 웹 앱, MinIO, pipeline 컨테이너를 올리는 방법
- 실습 전체에서 재사용할 날짜 partition 변수 `BOOTSTRAP_DATE`
- 모든 저장 계층을 먼저 관찰하기 위한 deterministic bootstrap 경로

#### 선수 조건

- Docker Desktop 또는 Docker Engine
- Docker Compose v2
- `git`, `bash` 또는 호환 shell

#### 깨끗한 상태로 시작하고 싶을 때

아래 명령은 컨테이너 volume과 생성 데이터를 지웁니다. 학습을 처음부터 다시 하고 싶을 때만 실행하세요.

```bash
docker compose down -v
rm -rf data/raw_spool/beacon_events warehouse/quiz.duckdb reports/quiz_pipeline_report.html
```

#### Compose 설정 검증과 서비스 실행

```bash
docker compose config
docker compose build
docker compose up -d minio createbuckets web
```

웹 앱 health check:

```bash
curl -fsS http://localhost:8000/health
```

브라우저에서 `http://localhost:8000`을 엽니다.

확인할 화면:

- 처음 접속하면 문제가 한꺼번에 보이지 않습니다.
- 메인 페이지에는 `문제 풀기` 버튼이 보입니다.
- `문제 풀기`를 누르면 세 문제 중 하나가 한 번에 하나만 표시됩니다.
- `답 제출`을 누르면 정답/오답이 보이고 `다음 문제` 버튼이 나타납니다.
- 각 문제에는 `문제 패스` 버튼이 있습니다.

#### 관찰용 데이터 bootstrap

2단계에서는 먼저 모든 계층을 눈으로 보기 위해 샘플 데이터를 한 번 생성합니다. 3단계에서 같은 흐름을 다시 한 줄씩 분해해서 배웁니다.

```bash
docker compose run --rm pipeline python scripts/init_quiz_db.py
export BOOTSTRAP_DATE=$(date -u +%F)
docker compose run --rm pipeline python scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite
docker compose run --rm pipeline python scripts/upload_logs_to_minio.py
docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py
docker compose run --rm pipeline dbt run --project-dir dbt_quiz --profiles-dir dbt_quiz
docker compose run --rm pipeline dbt test --project-dir dbt_quiz --profiles-dir dbt_quiz
```

샘플 이벤트는 아래 순서를 고정으로 만듭니다.

1. landing 접속
2. 첫 번째 문제 노출
3. 첫 번째 문제 정답 제출
4. 두 번째 문제 노출
5. 두 번째 문제 오답 제출
6. 세 번째 문제 노출
7. 세 번째 문제 패스
8. finish 도달

### 2.2 데이터를 확인하고 분석 해보기

#### 2.2.a DWH 데이터 확인

**이 단계에서 배우는 것**

- DuckDB 안에 raw/staging/fact/mart 테이블이 어떻게 보이는지
- dbt가 만든 모델을 SQL로 직접 확인하는 방법

```bash
docker compose run --rm pipeline python - <<'PY'
import duckdb
queries = {
    "raw event count": "select count(*) as raw_events from raw_beacon_events",
    "raw events by type": "select event_type, count(*) as cnt from raw_beacon_events group by 1 order by 1",
    "raw access-log fields": "select event_type, quiz_step, display_order, question_id from raw_beacon_events order by occurred_at_client",
    "staging preview": "select event_id, event_type, quiz_step, display_order, question_id, received_at_server from stg_beacon_events order by received_at_server limit 8",
    "summary mart": "select metric_name, metric_value from mart_quiz_summary order by metric_name",
    "access funnel": "select quiz_step, display_order, view_count, answer_count, skip_count, session_count from mart_access_log_funnel order by display_order nulls first, quiz_step",
}
with duckdb.connect('/workspace/warehouse/quiz.duckdb', read_only=True) as conn:
    for label, sql in queries.items():
        print(f"\n-- {label}")
        for row in conn.execute(sql).fetchall():
            print(row)
PY
```

확인할 파일/설정:

- `dbt_quiz/dbt_project.yml`: 모델 기본 materialization
- `dbt_quiz/models/sources.yml`: DuckDB raw source 선언
- `dbt_quiz/models/schema.yml`: not null, accepted values, access-log 테스트
- `dbt_quiz/models/staging/stg_beacon_events.sql`
- `dbt_quiz/models/marts/fct_quiz_events.sql`
- `dbt_quiz/models/marts/mart_access_log_funnel.sql`

#### 2.2.b DataLake 데이터 확인

**이 단계에서 배우는 것**

- JSONL raw 로그가 어떤 파일로 쌓이는지
- MinIO object key가 날짜 partition처럼 구성되는지
- DataLake raw zone은 “가공 전 원본 보존”을 위한 계층이라는 점

로컬 raw spool 확인:

```bash
find data/raw_spool/beacon_events -type f | sort
sed -n '1,8p' data/raw_spool/beacon_events/dt=$BOOTSTRAP_DATE/events.jsonl
```

MinIO CLI 확인:

```bash
docker compose run --rm --entrypoint /bin/sh createbuckets -c '
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
mc ls local/raw/beacon-events/ --recursive
'
```

MinIO Web UI 확인:

1. 브라우저에서 `http://localhost:9001` 접속
2. 로그인
   - Username: `minioadmin`
   - Password: `minioadmin`
3. **Object Browser**로 이동
4. bucket `raw` 선택
5. `beacon-events/dt=YYYY-MM-DD/events.jsonl` 경로 확인
6. object 크기/수정 시간 확인
7. 가능하면 Preview 또는 Download로 JSONL row 확인

이 화면은 현업에서 S3 Console, GCS Console, Azure Portal로 raw data lake를 확인하는 경험과 비슷합니다.

#### 2.2.c 어플리케이션 데이터 확인하기

**이 단계에서 배우는 것**

- SQLite의 `questions`는 제품 운영 데이터이고, beacon 로그는 행동 데이터라는 차이
- 두 데이터는 나중에 조인될 수 있지만 생성 목적이 다르다는 점

```bash
docker compose run --rm pipeline python - <<'PY'
import sqlite3
with sqlite3.connect('/workspace/app/data/quiz.sqlite3') as conn:
    conn.row_factory = sqlite3.Row
    for row in conn.execute('select id, prompt, correct_choice from questions order by id'):
        print(dict(row))
PY
```

#### 2.2.d 데이터 발생지점 확인하기

**이 단계에서 배우는 것**

- “쌓이는 로그”가 어떤 사용자 행동/코드 위치에서 만들어지는지
- 브라우저 이벤트와 서버 append 시점을 구분하는 법

| 사용자 행동/코드 위치 | 생성 이벤트 | 생성 순간 | 주요 필드 | 최종 raw 위치 |
| --- | --- | --- | --- | --- |
| 페이지 최초 진입 후 `beacon.js` 초기화 | `page_view` | landing 화면이 열릴 때 | `quiz_step='landing'`, `display_order=null` | `data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl` |
| `문제 풀기` 클릭 후 `showQuestion(...)` | `page_view` | 문제 하나가 화면에 표시될 때 | `quiz_step='question'`, `display_order=1` | 같은 JSONL |
| `다음 문제` 클릭 후 `showQuestion(...)` | `page_view` | 다음 문제가 표시될 때 | `display_order=2`, `display_order=3` | 같은 JSONL |
| `답 제출` 후 `submitAnswer(...)` | `answer_submitted` | `/api/answer` 응답 뒤 | `selected_choice`, `correct_choice`, `is_correct`, `quiz_step='question'` | 같은 JSONL |
| `문제 패스` 후 `skipQuestion(...)` | `question_skipped` | `/api/skip` 호출 뒤 | `skip_reason='next_question'`, `display_order` | 같은 JSONL |
| 마지막 문제 이후 `showFinish(...)` | `page_view` | finish 화면이 표시될 때 | `quiz_step='finish'`, `display_order=null` | 같은 JSONL |

열어볼 코드:

- `app/static/beacon.js`
  - `baseEvent(...)`
  - `showQuestion(...)`
  - `submitAnswer(...)`
  - `skipQuestion(...)`
  - `showFinish(...)`
- `app/app.py`
  - `/beacon`
  - `validate_event(...)`
  - `spool_event(...)`

---

## 3. 데이터의 연계: DataLake → DWH

**이 단계에서 배우는 것**

- raw spool과 MinIO object가 어떻게 연결되는지
- MinIO에 보존된 원본 로그가 DuckDB raw table로 적재되는지
- dbt가 raw table을 staging/fact/mart로 바꾸는지

3단계는 2단계 bootstrap에서 실행한 일을 한 줄씩 의미를 붙여 다시 실행합니다.

### 3.1 raw spool 생성

브라우저에서 직접 이벤트를 만들거나 deterministic sample을 사용합니다.

브라우저 방식:

```bash
open http://localhost:8000
# 문제 풀기 → 답 제출 → 다음 문제 → 문제 패스 등을 수행
```

샘플 방식:

```bash
export BOOTSTRAP_DATE=$(date -u +%F)
docker compose run --rm pipeline python scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite
```

### 3.2 DataLake raw zone으로 업로드

```bash
docker compose run --rm pipeline python scripts/upload_logs_to_minio.py
```

코드 읽기 포인트:

- `scripts/upload_logs_to_minio.py`
  - `object_key_for(...)`
  - `client.upload_file(...)`

### 3.3 DWH raw table로 적재

```bash
docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py
```

적재 결과 확인:

```bash
docker compose run --rm pipeline python - <<'PY'
import duckdb
with duckdb.connect('/workspace/warehouse/quiz.duckdb', read_only=True) as conn:
    print(conn.execute('select count(*) from raw_beacon_events').fetchall())
    print(conn.execute('describe raw_beacon_events').fetchall())
PY
```

코드 읽기 포인트:

- `scripts/load_minio_to_duckdb.py`
  - MinIO object listing
  - JSONL parsing
  - `raw_beacon_events` schema
  - `quiz_step`, `display_order` 컬럼 적재

### 3.4 dbt 모델 실행

```bash
docker compose run --rm pipeline dbt run --project-dir dbt_quiz --profiles-dir dbt_quiz
docker compose run --rm pipeline dbt test --project-dir dbt_quiz --profiles-dir dbt_quiz
```

여기서 `dbt run`은 모델을 만들고, `dbt test`는 이벤트 계약과 데이터 품질을 검증합니다.

---

## 4. 분석 요건에 맞춰 액세스 로그 추가하기

**이 단계에서 배우는 것**

- 분석 질문이 생기면 이벤트 계약이 어떻게 바뀌는지
- 단순 `page_view`만으로 부족할 때 어떤 필드를 추가해야 하는지
- 샘플 데이터, dbt 테스트, 검증 스크립트가 같은 계약을 바라봐야 한다는 점

### 4.1 분석 요건

우리가 알고 싶은 것은 단순히 “페이지를 봤다”가 아닙니다.

- 사용자가 landing에 도달했는가?
- 실제 문항이 몇 번째 순서로 노출됐는가?
- 답안 제출/패스가 몇 번째 문항 노출에서 발생했는가?
- finish까지 도달했는가?

그래서 `page_view`를 액세스 로그로 해석하고 다음 필드를 추가합니다.

| 필드 | 값 | 의미 |
| --- | --- | --- |
| `quiz_step` | `landing`, `question`, `finish` | 퀴즈 흐름의 어느 화면/단계에서 생긴 로그인지 |
| `display_order` | `1`, `2`, `3`, 또는 `null` | 한 세션 안에서 몇 번째로 노출된 문제인지. landing/finish는 문제 화면이 아니므로 `null` |

계약:

- `page_view`는 `landing`, `question`, `finish` 모두에서 발생합니다.
- `answer_submitted`는 항상 `quiz_step='question'`이어야 합니다.
- `question_skipped`는 항상 `quiz_step='question'`이어야 합니다.
- 문제에 묶인 `page_view`, `answer_submitted`, `question_skipped`는 `display_order`가 null이면 안 됩니다.

### 4.2 deterministic sample sequence

`scripts/generate_sample_events.py --overwrite`는 다음 8건을 만듭니다.

| 순서 | event_type | quiz_step | question_id | display_order | 비고 |
| --- | --- | --- | --- | --- | --- |
| 1 | `page_view` | `landing` | null | null | 메인 화면 접속 |
| 2 | `page_view` | `question` | 첫 번째 seeded question | 1 | 첫 문제 노출 |
| 3 | `answer_submitted` | `question` | 첫 번째 seeded question | 1 | 정답 제출 |
| 4 | `page_view` | `question` | 두 번째 seeded question | 2 | 두 번째 문제 노출 |
| 5 | `answer_submitted` | `question` | 두 번째 seeded question | 2 | 오답 제출 |
| 6 | `page_view` | `question` | 세 번째 seeded question | 3 | 세 번째 문제 노출 |
| 7 | `question_skipped` | `question` | 세 번째 seeded question | 3 | 문제 패스 |
| 8 | `page_view` | `finish` | null | null | 완료 화면 |

확인:

```bash
export BOOTSTRAP_DATE=$(date -u +%F)
docker compose run --rm pipeline python scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite
sed -n '1,8p' data/raw_spool/beacon_events/dt=$BOOTSTRAP_DATE/events.jsonl
```

### 4.3 클라이언트 코드에서 확인할 핵심 형태

`app/static/beacon.js`의 이벤트 payload는 아래 구조를 포함해야 합니다.

```js
baseEvent("page_view", questionId, {
  quiz_step: "question",
  display_order: displayOrder,
});

baseEvent("answer_submitted", questionId, {
  quiz_step: "question",
  display_order: displayOrder,
});

baseEvent("question_skipped", questionId, {
  quiz_step: "question",
  display_order: displayOrder,
});
```

landing/finish는 문제 화면이 아니므로 `question_id=null`, `display_order=null`입니다.

### 4.4 dbt mart 추가

`dbt_quiz/models/marts/mart_access_log_funnel.sql`은 액세스 로그를 퍼널 형태로 요약합니다.

```sql
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
```

직접 조회:

```bash
docker compose run --rm pipeline python - <<'PY'
import duckdb
with duckdb.connect('/workspace/warehouse/quiz.duckdb', read_only=True) as conn:
    for row in conn.execute('''
        select quiz_step, display_order, view_count, answer_count, skip_count, session_count
        from mart_access_log_funnel
        order by display_order nulls first, quiz_step
    ''').fetchall():
        print(row)
PY
```

---

## 5. dbt로 분석 가능한 모델 만들기

**이 단계에서 배우는 것**

- raw table을 그대로 분석하지 않고 staging/fact/mart로 나누는 이유
- dbt test로 이벤트 계약을 코드화하는 방법
- 분석 엔지니어링 영역과 데이터 엔지니어링 영역이 만나는 지점

모델 흐름:

```text
source raw_beacon_events
  → stg_beacon_events
  → fct_quiz_events
  → mart_quiz_summary
  → mart_quiz_summary_event_counts
  → mart_quiz_summary_answer_outcomes
  → mart_quiz_summary_skip_counts
  → mart_access_log_funnel
```

실행:

```bash
docker compose run --rm pipeline dbt run --project-dir dbt_quiz --profiles-dir dbt_quiz
docker compose run --rm pipeline dbt test --project-dir dbt_quiz --profiles-dir dbt_quiz
```

테스트 파일:

- `dbt_quiz/models/schema.yml`
  - `event_type` accepted values
  - `quiz_step` accepted values
  - 주요 컬럼 not null
- `dbt_quiz/tests/question_id_required.sql`
- `dbt_quiz/tests/is_correct_boolean.sql`
- `dbt_quiz/tests/question_events_display_order_required.sql`
- `dbt_quiz/tests/answer_skip_quiz_step_required.sql`
- `dbt_quiz/tests/answer_skip_display_order_required.sql`

질문:

- `stg_beacon_events`에서 타입 캐스팅을 하는 이유는 무엇일까요?
- `fct_quiz_events`에서 `answer_outcome`을 만드는 이유는 무엇일까요?
- mart를 여러 개로 나누면 어떤 장단점이 있을까요?

---

## 6. 최종 시각화와 검증

**이 단계에서 배우는 것**

- mart 결과를 사람이 읽을 수 있는 리포트로 바꾸는 법
- 간단한 시각화라도 파이프라인의 소비 지점을 명확히 해준다는 점
- 검증 스크립트가 전체 산출물을 어떻게 확인하는지

리포트 생성:

```bash
docker compose run --rm pipeline python scripts/render_report.py
```

브라우저에서 열기:

```bash
open reports/quiz_pipeline_report.html
```

리포트에서 확인할 섹션:

- 이벤트별 건수
- 정답/오답 제출 건수
- 문항별 skip 건수
- **접속/문항 노출 퍼널**

전체 검증:

```bash
docker compose run --rm pipeline python scripts/verify_pipeline.py
```

검증 스크립트는 최소한 다음을 확인합니다.

- SQLite에 질문 3개가 있는가?
- raw spool에 `page_view`, `answer_submitted`, `question_skipped`가 있는가?
- landing/question/finish `page_view`가 있는가?
- question-scoped 이벤트의 `display_order`가 1/2/3으로 들어갔는가?
- answer/skip 이벤트가 `quiz_step='question'`과 non-null `display_order`를 갖는가?
- MinIO object가 존재하는가?
- DuckDB raw table에 `quiz_step`, `display_order` 컬럼이 있는가?
- dbt가 `mart_access_log_funnel`을 만들었는가?
- HTML 리포트에 `접속/문항 노출 퍼널` 섹션이 있는가?

---

## 7. 전체 재실행과 확장 읽기

**이 단계에서 배우는 것**

- 파이프라인을 한 번에 재실행하는 방법
- deterministic sample로 같은 결과를 반복 생성하는 방법
- 이후 자신의 프로젝트에 적용할 때 읽어야 할 확장 주제

한 번에 실행:

```bash
docker compose run --rm pipeline bash scripts/run_full_pipeline.sh
```

이 스크립트는 기본적으로 deterministic sample을 위해 `data/raw_spool/beacon_events`와 MinIO `raw/beacon-events/` prefix를 정리한 뒤 다시 생성합니다. 브라우저에서 직접 만든 로그를 보존하며 실행하고 싶다면 다음처럼 실행하세요.

```bash
docker compose run --rm \
  -e RESET_SAMPLE_SPOOL=0 \
  -e CLEAR_RAW_PREFIX=0 \
  pipeline bash scripts/run_full_pipeline.sh
```

실습 종료:

```bash
docker compose down
```

완전히 초기화:

```bash
docker compose down -v
rm -rf data/raw_spool/beacon_events warehouse/quiz.duckdb reports/quiz_pipeline_report.html
```

확장 읽기:

- 이벤트 설계/A-B 테스트: [`docs/event-design-and-ab-testing.md`](docs/event-design-and-ab-testing.md)
- 데이터 엔지니어링 vs 분석 엔지니어링: [`docs/data-engineering-vs-analytics-engineering.md`](docs/data-engineering-vs-analytics-engineering.md)
- 웹 비콘 로그 자세히 보기: [`docs/web-beacon-logs.md`](docs/web-beacon-logs.md)
- 아키텍처 변형안: [`docs/pipeline-architecture.md`](docs/pipeline-architecture.md)

---

## 트러블슈팅

### `docker compose up`이 실패할 때

```bash
docker compose logs minio web
docker compose down
docker compose up -d minio createbuckets web
```

### 퀴즈 수가 3개가 아닐 때

```bash
docker compose run --rm pipeline python scripts/init_quiz_db.py
```

### raw spool이 비어 있을 때

브라우저에서 퀴즈를 한 번 풀거나 샘플 이벤트를 만듭니다.

```bash
export BOOTSTRAP_DATE=$(date -u +%F)
docker compose run --rm pipeline python scripts/generate_sample_events.py --date "$BOOTSTRAP_DATE" --overwrite
```

### MinIO에서 object가 안 보일 때

```bash
docker compose logs createbuckets
docker compose run --rm pipeline python scripts/upload_logs_to_minio.py
```

Web UI는 `http://localhost:9001`, 계정은 `minioadmin` / `minioadmin`입니다.

### DuckDB 적재가 실패할 때

```bash
docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py
```

MinIO에 object가 먼저 있어야 합니다.

### dbt 실행이 실패할 때

명령 순서를 확인하세요. `dbt` 옵션은 subcommand 뒤에 둡니다.

```bash
docker compose run --rm pipeline dbt run --project-dir dbt_quiz --profiles-dir dbt_quiz
docker compose run --rm pipeline dbt test --project-dir dbt_quiz --profiles-dir dbt_quiz
```

---

## 이 실습이 끝나면 설명할 수 있어야 하는 것

- 데이터 파이프라인이 왜 필요한지
- SQLite, JSONL spool, MinIO, DuckDB, dbt mart가 각각 어떤 책임을 갖는지
- 웹 비콘 로그가 어느 사용자 행동에서 생성되는지
- `quiz_step`, `display_order` 같은 필드가 분석 요건에서 어떻게 도출되는지
- DataLake에 보존된 raw 로그를 DWH로 연계하는 방법
- dbt 테스트와 검증 스크립트로 이벤트 계약을 지키는 방법
- 간단한 시각화가 데이터 파이프라인의 최종 소비 지점이 되는 이유
