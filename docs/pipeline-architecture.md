# 파이프라인 아키텍처와 선택 이유

## 왜 이 구조를 선택했는가

승인된 계획은 다음 원칙을 우선합니다.

1. 초심자가 각 경계를 눈으로 볼 수 있어야 한다.
2. Docker Compose와 스크립트만으로 재현 가능해야 한다.
3. MinIO, DuckDB, dbt, SQLite가 각각 분명한 역할을 가져야 한다.

그래서 이 저장소는 다음 구조를 기본안으로 채택합니다.

## 기본 아키텍처

```text
Browser
  └─ beacon.js
      └─ Flask /beacon
          ├─ SQLite (quiz questions)
          └─ local JSONL spool

local JSONL spool
  └─ upload_logs_to_minio.py
      └─ MinIO raw bucket/prefix

MinIO raw objects
  └─ load_minio_to_duckdb.py
      └─ DuckDB raw_beacon_events

DuckDB raw table
  └─ dbt
      ├─ stg_beacon_events
      ├─ fct_quiz_events
      ├─ mart_quiz_summary
      └─ mart_access_log_funnel

dbt output
  └─ render_report.py
      └─ reports/quiz_pipeline_report.html
```

## 이 구조의 장점

### 1. 수집 경계가 보인다

브라우저 이벤트가 바로 MinIO로 가지 않고, 먼저 로컬 spool 파일에 쌓입니다.  
학습자는 “앱이 로그를 만들었다”와 “로그를 저장소로 옮겼다”를 구분해서 볼 수 있습니다.

### 2. 각 도구의 책임이 분리된다

- **SQLite**: 앱의 작은 운영 데이터
- **MinIO**: raw object storage
- **DuckDB**: 로컬 analytical storage / query engine
- **dbt**: 모델링, 테스트, 재사용 가능한 계층화

### 3. 검증 지점이 많아진다

각 단계마다 “무엇이 생겨야 하는가?”를 확인할 수 있습니다.

- spool JSONL 파일
- MinIO object prefix
- DuckDB raw table
- dbt model/test
- access-log funnel mart
- HTML report

## raw 경로 규약

권장 raw object 규약:

```text
s3://raw/beacon-events/dt=YYYY-MM-DD/events.jsonl
```

권장 로컬 spool 규약:

```text
data/raw_spool/beacon_events/dt=YYYY-MM-DD/events.jsonl
```

이처럼 날짜 partition과 유사한 구조를 두면 학습자가 “partition-like layout”을 직관적으로 이해하기 쉽습니다.

## 액세스 로그 필드가 어디까지 흘러가는가

`quiz_step`과 `display_order`는 브라우저 payload에서 시작해 다음 계층을 그대로 통과합니다.

```text
beacon.js payload
  → raw JSONL
  → MinIO object
  → raw_beacon_events.quiz_step/display_order
  → stg_beacon_events
  → fct_quiz_events
  → mart_access_log_funnel
  → reports/quiz_pipeline_report.html의 "접속/문항 노출 퍼널"
```

이 구조를 보면 “새 분석 요건이 생겼을 때 필드가 어느 계층까지 반영되어야 하는가?”를 추적할 수 있습니다.

## 왜 Flask 앱이 MinIO에 직접 쓰지 않는가

가능한 대안:

1. Flask가 beacon 요청마다 바로 MinIO 업로드
2. 별도 collector 서비스가 이벤트를 받아 MinIO로 저장
3. 현재 선택안: Flask → 로컬 spool → 수동/배치 업로드

현재 실습에서는 3번을 선택합니다. 이유는 다음과 같습니다.

- 앱과 object storage 결합도를 낮춘다.
- raw 로컬 파일과 raw object storage를 따로 확인할 수 있다.
- “수집”과 “적재”를 서로 다른 단계로 학습할 수 있다.

## 나중에 확장할 수 있는 방향

### 확장 A: DuckDB가 MinIO를 직접 읽도록 만들기

- 장점: 적재 스크립트가 단순해질 수 있음
- 단점: 초심자에게는 S3/httpfs 설정이 먼저 어려울 수 있음

### 확장 B: collector 서비스 추가

- 장점: 실제 서비스 구조와 더 비슷함
- 단점: 현재 실습의 초점이 마이크로서비스 구성으로 이동할 수 있음

### 확장 C: near-real-time 파이프라인

- 장점: 이벤트 반영 속도가 빨라짐
- 단점: 현재 학습 목표인 “경계를 눈으로 본다”는 장점이 줄어들 수 있음

## 이 문서를 읽고 나서 확인할 질문

- 왜 raw 로그를 한 번 더 spool에 남기는가?
- SQLite와 DuckDB를 같은 DB로 합치지 않은 이유는 무엇인가?
- dbt는 단순 SQL 실행기와 무엇이 다른가?
- HTML 리포트가 왜 최종 목적물이 아니라 “검증 결과물”인가?

이 질문에 답할 수 있으면, 이 실습의 아키텍처 의도를 제대로 이해한 것입니다.
