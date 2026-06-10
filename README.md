# FinSight

## LangGraph 기반 Multi-Agent 금융 시장 브리핑 시스템

FinSight는 경제 뉴스와 주식 시장 데이터를 수집한 뒤, LangGraph 기반 Multi-Agent 시스템을 활용하여 시장 상황을 분석하고 AI 브리핑을 생성하는 프로젝트입니다.

수집된 데이터는 SQLite 데이터베이스에 저장되며, FastAPI를 통해 조회할 수 있고 Gmail을 통해 브리핑 결과를 이메일로 발송할 수 있습니다.

---

# 프로젝트 목표

기존 금융 정보 서비스는 사용자가 직접 뉴스와 시장 데이터를 분석해야 하는 불편함이 있습니다.

FinSight는 최신 뉴스와 시장 데이터를 수집하고 AI Agent가 분석하여 핵심 정보를 요약함으로써 사용자의 의사결정을 지원하는 것을 목표로 합니다.

---

# 주요 기능

## 시장 데이터 수집

* PyKRX 기반 주식 데이터 수집
* 현재가 조회
* 1개월 수익률 계산
* 3개월 수익률 계산
* 1년 수익률 계산

## 뉴스 수집

* RSS 기반 뉴스 수집
* 경제 뉴스 수집
* 산업 뉴스 수집
* 중복 기사 제거

## Multi-Agent 분석

### Macro Agent

경제 뉴스와 시장 상황을 종합 분석

### Sector Agent

시장 데이터 및 종목 흐름 분석

### Summary Agent

Macro Agent와 Sector Agent 결과를 종합하여 최종 브리핑 생성

## LangGraph Workflow

여러 Agent를 하나의 Workflow로 연결하여 분석 프로세스 수행

## 데이터 저장

* SQLite 저장
* 브리핑 이력 관리

## API 제공

FastAPI 기반 REST API 제공

## 이메일 발송

Gmail SMTP를 활용한 AI 브리핑 이메일 발송

---

# 시스템 아키텍처

```text
뉴스 수집
      │
시장 데이터 수집
      │
      ▼
 LangGraph
 ├ Macro Agent
 ├ Sector Agent
 └ Summary Agent
      │
      ▼
 AI 브리핑 생성
      │
 ┌────┴────┐
 ▼         ▼
DB 저장   이메일 발송
      │
      ▼
 FastAPI 조회
```

---

# 프로젝트 구조

```text
app/
├── agents/
├── api/
├── collectors/
├── db/
├── graph/
├── services/
```

### agents

AI Agent 구현

### collectors

뉴스 및 시장 데이터 수집

### graph

LangGraph Workflow 정의

### db

SQLite 모델 및 데이터베이스 관리

### services

브리핑 생성 및 이메일 발송 로직

### api

FastAPI 엔드포인트

---

# 기술 스택

## Backend

* Python
* FastAPI

## AI

* Ollama
* LangGraph

## Database

* SQLite
* SQLAlchemy

## Data Collection

* PyKRX
* Feedparser

## Email

* Gmail SMTP
* Python-Dotenv

---

# API 예시

## 브리핑 생성

```http
GET /briefing
```

## 브리핑 목록 조회

```http
GET /briefing/history
```

## 브리핑 상세 조회

```http
GET /briefing/{id}
```

---

# 실행 방법

## 저장소 클론

```bash
git clone <repository_url>
cd FinSight
```

## 가상환경 생성

```bash
python -m venv venv
```

## 가상환경 활성화

```bash
venv\Scripts\activate
```

## 패키지 설치

```bash
pip install -r requirements.txt
```

## 서버 실행

```bash
uvicorn app.main:app --reload
```

## Swagger 접속

```text
http://127.0.0.1:8000/docs
```

---

# 결과 예시

## AI 브리핑 생성

* 시장 데이터 분석
* 뉴스 분석
* Multi-Agent 분석
* 최종 브리핑 생성

## 이메일 발송

생성된 브리핑을 Gmail로 발송

## 브리핑 저장

SQLite 데이터베이스에 저장 후 API로 조회 가능

> Swagger 실행 화면, 이메일 수신 화면, 브리핑 결과 화면 스크린샷 첨부 예정

---

# 현재 한계

* Watchlist 기반 종목 분석
* 연합뉴스 중심 뉴스 수집
* 수동 실행 방식
* 웹 대시보드 미구현

---

# 향후 개선 계획

## 시장 주도주 자동 탐색

고정 Watchlist 제거 후 거래대금 상위 종목 자동 수집

## 뉴스-종목 연관 분석

뉴스와 관련 종목을 자동 매핑하여 분석 정확도 향상

## 자동 스케줄링

매일 정해진 시간에 브리핑 자동 생성 및 이메일 발송

## 웹 대시보드

AI 브리핑 조회 및 시각화 기능 제공

## 뉴스 소스 확장

다양한 경제 뉴스 소스 추가
