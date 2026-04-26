# 데이터 파이프라인 실습: Beacon 로그로 배우는 Hands-on Lab

> 이 README는 승인된 계획(`.omx/plans/plan-data-pipeline-hands-on-beacon-logs.md`)을 기준으로 작성한 **실습 경로 계약서**입니다.  
> 현재 저장소는 greenfield 상태이므로, 아래 단계와 명령은 구현이 충족해야 할 목표 경로를 문서로 먼저 고정합니다.

## 이 실습의 목표

이 실습은 “사용자 행동 로그가 어떻게 데이터가 되는가?”를 눈으로 확인하는 데 초점을 둡니다.  
학습자는 아주 단순한 퀴즈 웹 앱에서 시작해 다음 흐름을 끝까지 따라갑니다.

1. 브라우저가 beacon 이벤트를 보냅니다.
2. Flask 앱이 JSONL raw 로그를 로컬 spool에 적재합니다.
3. raw 로그를 MinIO로 업로드합니다.
4. MinIO의 raw 로그를 DuckDB로 적재합니다.
5. dbt로 staging/mart 모델을 만듭니다.
6. 최종 HTML 리포트를 열어 파이프라인 결과를 확인합니다.

## 학습 범위와 문서 경계

- **README 본문**: 데이터 엔지니어링 경로
  - 서비스 실행
  - SQLite 시드 데이터
  - beacon 이벤트 생성
  - raw spool / MinIO / DuckDB / dbt / report 검증
- **`docs/` 보조 문서**: 분석 엔지니어링/이벤트 설계 확장 주제
  - 데이터 엔지니어링 vs 분석 엔지니어링
  - 이벤트 설계 기초
  - 메트릭/A-B 테스트 확장
  - 아키텍처 변형안

보조 읽을거리:

- [`docs/data-engineering-vs-analytics-engineering.md`](docs/data-engineering-vs-analytics-engineering.md)
- [`docs/event-design-and-ab-testing.md`](docs/event-design-and-ab-testing.md)
- [`docs/pipeline-architecture.md`](docs/pipeline-architecture.md)

## 목표 아키텍처

```text
브라우저 퀴즈 페이지
  └─ beacon.js
      └─ POST /beacon (Flask)
          ├─ SQLite: app/data/quiz.sqlite3
          └─ JSONL spool: data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl

Learner commands
  ├─ scripts/upload_logs_to_minio.py
  │   └─ s3://raw/beacon-events/dt=YYYY-MM-DD/
  ├─ scripts/load_minio_to_duckdb.py
  │   └─ warehouse/quiz.duckdb
  ├─ dbt run / dbt test
  └─ scripts/render_report.py
      └─ reports/quiz_pipeline_report.html
```

## 구현 완료 후 기대 파일 구조

```text
README.md
docker-compose.yml
.env.example
app/
  Dockerfile
  app.py
  requirements.txt
  templates/index.html
  static/beacon.js
  data/
scripts/
  init_quiz_db.py
  generate_sample_events.py
  upload_logs_to_minio.py
  load_minio_to_duckdb.py
  render_report.py
  verify_pipeline.py
  run_full_pipeline.sh
pipeline/
  Dockerfile
  requirements.txt
dbt_quiz/
  dbt_project.yml
  profiles.yml.example
  models/
docs/
  data-engineering-vs-analytics-engineering.md
  event-design-and-ab-testing.md
  pipeline-architecture.md
data/raw_spool/
warehouse/
reports/
```

## 선수 조건

- Docker / Docker Compose
- 브라우저
- Python 기반 스크립트를 실행할 수 있는 환경(주 실행 경로는 Compose 내부)

기본 포트/환경 변수 계약:

- `WEB_PORT=8000`
- `MINIO_API_PORT=9000`
- `MINIO_CONSOLE_PORT=9001`

## 실습 경로

아래 명령은 **구현 완료 후** 그대로 동작해야 하는 체크포인트입니다.

### 1) Compose 설정 검증

**지금 어떤 경계를 넘었나?**  
로컬 실습 환경이 같은 방식으로 올라올 수 있는지 먼저 확인합니다.

```bash
docker compose config
docker compose build
```

기대 결과:

- Compose 파싱 성공
- `web`, `pipeline` 이미지 빌드 성공

### 2) MinIO와 웹 앱 실행

**지금 어떤 경계를 넘었나?**  
“사용자 행동이 발생하는 애플리케이션”과 “raw 로그가 저장될 오브젝트 스토리지”를 띄웁니다.

```bash
docker compose up -d minio createbuckets web
curl http://localhost:8000/health
```

기대 결과:

- `http://localhost:8000/health` → `{"status":"ok"}`

### 3) SQLite 퀴즈 데이터 초기화

**지금 어떤 경계를 넘었나?**  
로그를 발생시킬 최소한의 제품 데이터(퀴즈 3개)를 준비합니다.

```bash
docker compose run --rm pipeline python scripts/init_quiz_db.py
docker compose run --rm pipeline python -c "import sqlite3; print(sqlite3.connect('/workspace/app/data/quiz.sqlite3').execute('select count(*) from questions').fetchone()[0])"
```

기대 결과:

- 질문 수가 정확히 `3`

### 4) 퀴즈 앱 접속과 beacon 이벤트 생성

**지금 어떤 경계를 넘었나?**  
이제 데이터 엔지니어링 파이프라인의 출발점인 “사용자 행동”이 실제 로그로 남습니다.

브라우저에서 다음을 수행합니다.

1. `http://localhost:8000` 접속
2. 정답 1회 제출
3. 오답 1회 제출
4. 질문 1개 건너뛰기

또는 샘플 이벤트 생성 스크립트를 사용합니다.

```bash
docker compose run --rm pipeline python scripts/generate_sample_events.py
```

기대 결과:

- `page_view`
- `answer_submitted` (`is_correct=true/false` 둘 다 포함)
- `question_skipped`

### 5) 로컬 raw spool 확인

**지금 어떤 경계를 넘었나?**  
애플리케이션 로그가 먼저 “로컬 raw 이벤트”로 남는 지점을 확인합니다.

```bash
find data/raw_spool -type f | sort
head -n 5 data/raw_spool/beacon_events/dt=*/events.jsonl
```

기대 결과:

- `data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl` 존재
- JSONL row가 1개 이상 존재

### 6) MinIO로 raw 로그 업로드

**지금 어떤 경계를 넘었나?**  
파일 기반 raw 로그를 오브젝트 스토리지 계층으로 옮깁니다.

```bash
docker compose run --rm pipeline python scripts/upload_logs_to_minio.py
```

MinIO 안에서 기대하는 prefix:

```text
s3://raw/beacon-events/dt=YYYY-MM-DD/
```

가능하면 다음도 함께 확인합니다.

```bash
docker compose run --rm pipeline mc ls local/raw/beacon-events/ --recursive
```

### 7) DuckDB 적재

**지금 어떤 경계를 넘었나?**  
raw 로그를 분석 가능한 로컬 analytical store로 적재합니다.

```bash
docker compose run --rm pipeline python scripts/load_minio_to_duckdb.py
```

기대 결과:

- `warehouse/quiz.duckdb` 생성
- `raw_beacon_events` 테이블 생성

### 8) dbt 모델 실행

**지금 어떤 경계를 넘었나?**  
raw 로그를 staging/fact/mart 계층의 재사용 가능한 데이터 모델로 바꿉니다.

```bash
docker compose run --rm pipeline dbt --project-dir dbt_quiz --profiles-dir dbt_quiz run
docker compose run --rm pipeline dbt --project-dir dbt_quiz --profiles-dir dbt_quiz test
```

기대 결과:

- `stg_beacon_events`
- `fct_quiz_events`
- `mart_quiz_summary`
- dbt 테스트 모두 성공

### 9) 최종 리포트 생성

**지금 어떤 경계를 넘었나?**  
모델링된 데이터가 실제로 읽을 수 있는 결과물인지 확인합니다.

```bash
docker compose run --rm pipeline python scripts/render_report.py
```

기대 결과:

- `reports/quiz_pipeline_report.html` 생성
- 이벤트 수, 정답/오답 수, 스킵 수가 비어 있지 않음

### 10) 전체 재생 래퍼 실행

**지금 어떤 경계를 넘었나?**  
학습이 끝난 뒤, 전체 파이프라인을 한 번에 다시 재생해볼 수 있어야 합니다.

```bash
docker compose run --rm pipeline bash scripts/run_full_pipeline.sh
```

> `run_full_pipeline.sh`는 **주 학습 경로가 아니라** 복습/재생용 래퍼입니다.

### 11) 최종 검증 스크립트 실행

**지금 어떤 경계를 넘었나?**  
애플리케이션, raw 로그, MinIO, DuckDB, dbt, 리포트까지 모두 연결되었는지 기계적으로 확인합니다.

```bash
docker compose run --rm pipeline python scripts/verify_pipeline.py
```

검증 스크립트가 반드시 확인해야 할 항목:

- SQLite 질문 수가 정확히 3개
- raw spool에 JSONL row 존재
- `page_view`, `answer_submitted`, `question_skipped` 존재
- 공통 필드 존재:
  - `event_id`
  - `schema_version`
  - `session_id`
  - `anonymous_user_id`
  - `occurred_at_client`
  - `received_at_server`
  - `event_type`
- `answer_submitted`에는 `is_correct=true/false` 둘 다 존재
- MinIO raw object 존재
- DuckDB 및 dbt 산출물 존재
- HTML 리포트 존재 및 값이 비어 있지 않음

## 이벤트 계약

모든 이벤트는 최소한 다음 필드를 가져야 합니다.

- `event_id`
- `event_type`
- `schema_version`
- `session_id`
- `anonymous_user_id`
- `occurred_at_client`
- `received_at_server`
- `page_url`
- `user_agent`

이벤트별 추가 필드:

- `page_view`
  - `question_id` (optional)
  - `referrer` (optional)
- `answer_submitted`
  - `question_id`
  - `selected_choice`
  - `correct_choice`
  - `is_correct`
- `question_skipped`
  - `question_id`
  - `skip_reason`

## 트러블슈팅 가이드

### `docker compose up`이 실패할 때

- `.env.example`의 포트가 이미 사용 중인지 확인합니다.
- Docker Desktop / Docker daemon이 실행 중인지 확인합니다.

### 퀴즈 수가 3개가 아닐 때

- `scripts/init_quiz_db.py`를 다시 실행합니다.
- `app/data/quiz.sqlite3`를 삭제 후 재생성하는 reset 절차를 문서화합니다.

### raw spool이 비어 있을 때

- 브라우저 동작 대신 `scripts/generate_sample_events.py`를 사용합니다.
- `navigator.sendBeacon` 실패 시 `fetch` fallback이 동작하는지 확인합니다.

### MinIO에서 object가 안 보일 때

- bucket 이름과 prefix가 `raw/beacon-events/dt=YYYY-MM-DD/` 규약을 따르는지 확인합니다.
- MinIO 콘솔(`http://localhost:9001`) 또는 `mc ls`로 확인합니다.

### dbt 실행이 실패할 때

- `DBT_PROFILES_DIR=dbt_quiz` 설정 또는 `--profiles-dir dbt_quiz` 사용 여부를 확인합니다.
- DuckDB 파일 경로가 `warehouse/quiz.duckdb`인지 확인합니다.

## 이 실습이 끝나면 설명할 수 있어야 하는 것

- 앱 로그와 raw 로그의 차이
- raw object storage와 analytical store의 역할 차이
- DuckDB와 dbt가 파이프라인에서 각각 어떤 책임을 가지는지
- 왜 분석 엔지니어링 주제를 `docs/`로 분리했는지

## 다음 읽을거리

- 데이터 엔지니어링 vs 분석 엔지니어링 경계:
  [`docs/data-engineering-vs-analytics-engineering.md`](docs/data-engineering-vs-analytics-engineering.md)
- 이벤트 설계와 A/B 테스트 확장:
  [`docs/event-design-and-ab-testing.md`](docs/event-design-and-ab-testing.md)
- 아키텍처 선택 이유와 확장안:
  [`docs/pipeline-architecture.md`](docs/pipeline-architecture.md)
