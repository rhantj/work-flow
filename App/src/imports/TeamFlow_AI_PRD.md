# TeamFlow AI PRD

## 1. 문서 정보

| 항목 | 내용 |
| --- | --- |
| 문서명 | TeamFlow AI Product Requirements Document |
| 버전 | v1.0 |
| 목적 | 팀원이 같은 기준으로 제품 범위, 기능 요구사항, 권한 정책, 기술 구조를 이해하도록 정의 |
| 개발 기간 | 약 1개월 |
| 대상 서비스 | 대학생 팀프로젝트, 캡스톤디자인, 해커톤, AI 경진대회, 공모전 참가팀을 위한 AI 협업 및 평가 보조 웹 |

## 2. 제품 한 줄 정의

TeamFlow AI는 제한된 기간 안에 팀이 결과물을 제출해야 하는 프로젝트에서 회의록, 업무, 일정, 문서, GitHub 기록, 산출물, 개인별 기여도 근거를 AI가 연결해주는 협업 및 평가 보조 플랫폼이다.

## 3. 제품 배경

대학생 팀프로젝트, 캡스톤, 해커톤, 경진대회, 공모전은 대부분 짧은 기간 안에 팀이 결과물을 만들어 제출해야 한다. 이 과정에서 회의 내용, 역할 분담, 마감일, 개발 기록, 문서 작성, 발표자료 준비가 여러 도구에 흩어진다.

기존 협업툴은 업무 관리와 프로젝트 추적에는 강하지만, 학생 팀프로젝트에서 중요한 발표자료, 보고서, 제출 체크리스트, 팀원별 기여도 근거, 심사자 평가 보조 흐름까지 한 번에 제공하지는 않는다.

TeamFlow AI는 기존에 기획한 회의록 AI, AI Assistant, 대시보드, GitHub 관리, 산출물 생성 기능을 유지하면서, 심사자 전용 기여도 평가 보조 기능을 추가해 교육 및 대회 환경에 특화한다.

## 4. 해결하려는 문제

| 문제 | 설명 |
| --- | --- |
| 회의 정리 부담 | 회의 후 요약, 결정사항, 담당자, 마감일을 사람이 다시 정리해야 함 |
| 역할 분담 불명확 | 누가 무엇을 맡았는지 회의록, 메신저, 문서에 흩어짐 |
| 일정 관리 어려움 | 제출일, 발표일, 중간보고 일정과 세부 업무 마감이 연결되지 않음 |
| 산출물 준비 지연 | 발표자료, 보고서, README, 제안서가 마지막에 급하게 만들어짐 |
| 개발 기록 분리 | GitHub 커밋, PR, issue가 프로젝트 업무 및 보고서와 연결되지 않음 |
| 기여도 판단 어려움 | 교수, 조교, 심사자가 팀원별 실제 기여도를 객관적으로 확인하기 어려움 |
| 무임승차 문제 | 업무 수행 기록과 산출물 기여 기록이 남지 않아 공정한 평가가 어려움 |

## 5. 목표 사용자

| 사용자 | 니즈 |
| --- | --- |
| 팀장 | 프로젝트 생성, 팀원 초대, 역할 배정, 일정 관리, 산출물 준비, 팀 진행 상황 확인 |
| 팀원 | 내 업무 확인, 회의록 확인, 개인 To-Do 수행, 문서/산출물 공동 작업 |
| 심사자 | 교수, 조교, 심사위원. 팀별 진행 상황, 개인별 기여도 근거, 최종 평가 보조 자료 확인 |

## 6. 핵심 가치

| 가치 | 설명 |
| --- | --- |
| 자동 정리 | 회의록, 녹음, 영상에서 요약, To-Do, 일정, 위험요소를 자동 추출 |
| 프로젝트 맥락 AI | AI Assistant가 프로젝트 안의 회의록, 문서, 업무, GitHub, 산출물을 참고 |
| 제출 중심 관리 | 발표자료, 보고서, README, 제안서 등 최종 산출물 생성을 지원 |
| 기여도 근거화 | To-Do, 회의록, GitHub, 문서 기록을 바탕으로 심사자용 기여도 근거 제공 |
| 권한 분리 | 학생 협업 데이터와 심사자 평가 데이터를 역할별로 분리 |

## 7. 제품 범위

### 7.1 MVP 포함 범위

- 회원가입/로그인
- 프로젝트 생성 및 팀원 초대
- 역할 구분: 팀장, 팀원, 심사자
- 회의록 문서 업로드
- AI 회의 요약
- To-Do 자동 생성
- 기본 대시보드
- AI Assistant 기본 질문 답변
- 산출물 초안 생성
- 심사자 전용 기여도 리포트 기본 버전
- 최종 평가 점수 공개/비공개 정책 설계

### 7.2 MVP 이후 확장 범위

- 녹음파일 STT
- 영상파일 음성 추출
- 문서 RAG Q&A
- GitHub Repository 연동
- 커밋/PR/issue 요약
- 댓글, 개인 코멘트, 팀 코멘트
- AI 평가 근거 출처 표시 고도화
- PPT/PDF 자동 생성
- AI 경진대회 실험 로그 및 리더보드 기록

### 7.3 제외 범위

- 실시간 공동 문서 편집
- 모바일 앱
- 결제 기능
- 외부 메신저 완전 대체
- 복잡한 조직 단위 권한 관리
- AI에 의한 최종 자동 채점

## 8. 사용자 역할 및 접근 제어

| 기능 | 팀장 | 팀원 | 심사자 |
| --- | --- | --- | --- |
| 회의록 | 가능 | 가능 | 가능 |
| To-Do | 가능 | 가능 | 가능 |
| 대시보드 | 가능 | 가능 | 가능 |
| 개인별 기여도 리포트 | 불가 | 불가 | 가능 |
| 개인 코멘트 | 가능 | 가능 | 가능 |
| 팀 코멘트 작성/관리 | 가능 | 불가 | 가능 |
| 최종 평가 점수 | 공개 설정 시 가능 | 공개 설정 시 가능 | 가능 |
| AI 평가 근거 | 불가 | 불가 | 가능 |

### 접근 제어 원칙

- 회의록, To-Do, 대시보드는 모든 역할이 접근 가능하다.
- 개인별 기여도 리포트와 AI 평가 근거는 심사자만 접근 가능하다.
- 최종 평가 점수는 심사자가 공개로 설정한 경우에만 팀장과 팀원이 볼 수 있다.
- 개인 코멘트는 작성할 수 있으나 공개 범위는 작성자, 대상자, 심사자 중심으로 제한한다.
- 팀 코멘트는 팀장과 심사자가 작성 및 관리한다.
- AI는 최종 평가 점수를 확정하지 않고 평가 판단 근거만 제공한다.

## 9. 핵심 사용자 흐름

### 9.1 팀 프로젝트 시작 흐름

1. 팀장이 프로젝트를 생성한다.
2. 프로젝트 유형을 선택한다: 팀프로젝트, 캡스톤, 해커톤, AI 경진대회, 공모전.
3. 팀원이 초대 링크 또는 초대 코드로 참여한다.
4. 심사자는 수업 코드, 대회 코드, 관리자 초대로 연결된다.
5. 팀장은 프로젝트 마감일, 발표일, 제출물을 입력한다.

### 9.2 회의록 기반 업무 생성 흐름

1. 팀원이 회의록 문서를 업로드한다.
2. AI가 회의 요약, 결정사항, 위험요소, To-Do, 일정 후보를 생성한다.
3. 팀장 또는 팀원이 AI 결과를 검토한다.
4. 승인된 To-Do는 그룹/개인 업무로 저장된다.
5. 일정 후보는 캘린더와 대시보드에 반영된다.
6. 기여도 리포트는 추후 To-Do 수행 기록을 참고한다.

### 9.3 AI Assistant 사용 흐름

1. 사용자가 어느 화면에서든 AI Assistant를 연다.
2. 사용자가 프로젝트 관련 질문을 입력한다.
3. Assistant가 질문 유형을 분류한다.
4. DB, 문서, 회의록, GitHub, 산출물 데이터를 조회한다.
5. LLM이 답변을 생성한다.
6. 가능한 경우 출처를 함께 표시한다.

### 9.4 심사자 기여도 확인 흐름

1. 심사자가 담당 프로젝트 또는 팀 목록에 접근한다.
2. 팀별 진행률, 산출물 상태, 위험 신호를 확인한다.
3. 개인별 기여도 리포트를 연다.
4. To-Do, 회의록, GitHub, 문서 기록 기반 근거를 확인한다.
5. 필요 시 개인/팀 코멘트를 작성한다.
6. 최종 평가 점수를 입력하고 공개 여부를 설정한다.

## 10. 기능 요구사항

### FR-01 인증 및 사용자 관리

| 항목 | 내용 |
| --- | --- |
| 설명 | 이메일, 비밀번호, 이름 기반 회원가입과 로그인 제공 |
| 상세 요구사항 | JWT 기반 인증, 사용자 역할 저장, 프로젝트별 권한 검사 |
| 우선순위 | P0 |
| 기술 | Spring Boot, Java, Spring Security, JWT, MySQL/PostgreSQL |

### FR-02 프로젝트 생성 및 팀 관리

| 항목 | 내용 |
| --- | --- |
| 설명 | 팀장이 프로젝트를 생성하고 팀원 및 심사자를 초대 |
| 상세 요구사항 | 프로젝트 유형, 마감일, 발표일, 설명, 제출물 목록 입력 |
| 우선순위 | P0 |
| 기술 | Spring Boot REST API, DB, RBAC |

### FR-03 회의록 AI

| 항목 | 내용 |
| --- | --- |
| 설명 | 회의록 문서, 녹음파일, 영상파일을 기반으로 회의 내용을 구조화 |
| 상세 요구사항 | 요약, 결정사항, 위험요소, To-Do, 일정 후보 추출 |
| 우선순위 | 문서 업로드 P0, 음성/영상 P1 |
| 기술 | LLM, Deep Learning STT, Whisper, FFmpeg, 파일 파싱 |

### FR-04 To-Do 관리

| 항목 | 내용 |
| --- | --- |
| 설명 | AI가 생성한 업무를 팀/개인 To-Do로 저장하고 상태 관리 |
| 상세 요구사항 | 담당자, 제목, 마감일, 상태, 우선순위, 출처 회의록 저장 |
| 우선순위 | P0 |
| 기술 | Spring Boot REST API, DB |

### FR-05 대시보드

| 항목 | 내용 |
| --- | --- |
| 설명 | 프로젝트 진행률과 위험 상태를 직관적으로 표시 |
| 상세 요구사항 | 전체 진행률, 마감 임박, 지연 업무, 담당자별 업무량, 산출물 준비율 |
| 우선순위 | P0 |
| 기술 | DB Aggregation, Scoring Model, Chart.js/Recharts |

### FR-06 AI Assistant

| 항목 | 내용 |
| --- | --- |
| 설명 | 프로젝트 데이터 기반 질문 답변 및 업무 실행 지원 |
| 상세 요구사항 | 회의록, To-Do, 일정, 문서, GitHub, 산출물 기반 답변 |
| 우선순위 | P0 |
| 기술 | LLM, RAG, Embedding, Vector DB, Function Calling |

### FR-07 문서/RAG

| 항목 | 내용 |
| --- | --- |
| 설명 | 업로드 문서를 기반으로 질문 답변 제공 |
| 상세 요구사항 | PDF/TXT/DOCX 업로드, chunking, embedding, 검색, 출처 표시 |
| 우선순위 | P1 |
| 기술 | RAG, Embedding, Vector DB, pdfplumber, python-docx |

### FR-08 GitHub 관리

| 항목 | 내용 |
| --- | --- |
| 설명 | 개발 프로젝트의 GitHub 기록을 프로젝트 진행 데이터로 연결 |
| 상세 요구사항 | Repository 등록, commit/PR/issue 조회, AI 요약, To-Do 연결 |
| 우선순위 | P1 |
| 기술 | GitHub REST API/GraphQL API, Webhook, LLM |

### FR-09 산출물 생성

| 항목 | 내용 |
| --- | --- |
| 설명 | 프로젝트 데이터를 기반으로 발표자료, 보고서, README, 제안서 초안 생성 |
| 상세 요구사항 | 산출물 유형 선택, 포함 데이터 선택, 초안 생성, 저장 |
| 우선순위 | P0 기본 초안, P2 파일 다운로드 |
| 기술 | LLM, RAG, Template Engine, ReportLab, python-pptx |

### FR-10 기여도 평가 보조

| 항목 | 내용 |
| --- | --- |
| 설명 | 심사자 전용 개인별 기여도 판단 근거를 생성 |
| 상세 요구사항 | To-Do, 회의록, GitHub, 문서, 댓글 기반 근거 요약 |
| 우선순위 | P0 기본 리포트, P1 출처 고도화 |
| 기술 | DB Aggregation, LLM, Scoring Model, Machine Learning 확장 |

### FR-11 코멘트

| 항목 | 내용 |
| --- | --- |
| 설명 | 개인 코멘트와 팀 코멘트를 작성하고 권한별로 접근 |
| 상세 요구사항 | 개인 코멘트는 모두 작성 가능, 팀 코멘트 관리는 팀장/심사자 |
| 우선순위 | P1 |
| 기술 | Spring Boot REST API, DB, RBAC |

### FR-12 평가 점수 공개 설정

| 항목 | 내용 |
| --- | --- |
| 설명 | 심사자가 최종 평가 점수를 입력하고 공개 여부를 제어 |
| 상세 요구사항 | 비공개 기본값, 공개 시 학생 확인 가능, 수정 이력 저장 |
| 우선순위 | P1 |
| 기술 | DB, Audit Log, RBAC |

## 11. 비기능 요구사항

| 항목 | 요구사항 |
| --- | --- |
| 보안 | JWT 인증, RBAC, 프로젝트 단위 권한 검사, 평가 데이터 별도 접근 제어 |
| 개인정보 | 평가 데이터와 AI 근거는 심사자만 접근, 접근 로그 저장 |
| 성능 | 대시보드 기본 조회 2초 이내, 일반 AI 응답 15초 이내 목표 |
| 안정성 | AI 실패 시 재시도 또는 수동 입력 가능 |
| 추적성 | AI가 생성한 To-Do, 일정, 기여도 근거에는 출처 저장 |
| 사용성 | 팀원이 설명 없이 프로젝트 현황과 내 업무를 확인할 수 있어야 함 |
| 확장성 | GitHub, RAG, STT, PPT 생성은 모듈 단위로 확장 가능해야 함 |

## 12. 기술 스택

| 영역 | 추천 기술 |
| --- | --- |
| Frontend | React 또는 Next.js, TypeScript, Tailwind CSS |
| Backend | Spring Boot, Java, Spring Security, Spring Data JPA 또는 MyBatis |
| AI Backend | Python, Flask 또는 FastAPI, LLM/RAG/STT 처리용 API 서버 |
| Database | MySQL 또는 PostgreSQL |
| AI/LLM | OpenAI API 또는 기타 LLM API |
| STT/Deep Learning | Whisper 또는 STT API |
| RAG | Embedding, Vector DB, chunking |
| Vector DB | Chroma, FAISS, pgvector 중 선택 |
| ML/Scoring | 지연 위험도, 업무 편중, 기여도 이상치 탐지 |
| File Processing | pdfplumber, python-docx, FFmpeg |
| GitHub | GitHub REST API, GraphQL API, Webhook |
| Visualization | Chart.js, Recharts |
| Auth/Security | Spring Security, JWT, RBAC, Audit Log |
| Output | ReportLab, python-pptx, Google Slides API |

### 권장 서비스 구조

| 구성 | 역할 |
| --- | --- |
| React/Next.js Frontend | 사용자 화면, 대시보드, 회의록 업로드, Assistant, 심사자 화면 |
| Spring Boot Main Backend | 인증, 권한, 프로젝트, To-Do, 대시보드, GitHub, 평가 데이터 등 핵심 비즈니스 API |
| Python AI Backend | 회의록 요약, RAG, STT, 산출물 생성, 기여도 근거 요약 등 AI 처리 |
| MySQL/PostgreSQL | 서비스 핵심 데이터 저장 |
| Vector DB | 문서 chunk, embedding, RAG 검색 |
| Redis/Queue | AI 처리, 파일 처리, GitHub 동기화 같은 비동기 작업 |

## 13. 데이터 모델 초안

| 테이블 | 주요 필드 | 용도 |
| --- | --- | --- |
| users | id, email, password_hash, name | 사용자 |
| projects | id, title, type, deadline, description | 프로젝트 |
| project_members | id, project_id, user_id, role | 팀장/팀원/심사자 권한 |
| meetings | id, project_id, file_path, transcript, created_at | 회의록 |
| meeting_summaries | id, meeting_id, summary, decisions, risks | AI 회의 요약 |
| tasks | id, project_id, assignee_id, title, status, due_date, priority | To-Do |
| documents | id, project_id, filename, file_type, file_path | 문서 |
| document_chunks | id, document_id, chunk_text, embedding_id, page_number | RAG 검색 단위 |
| github_records | id, project_id, type, title, author, url, summary | 커밋/PR/issue |
| deliverables | id, project_id, type, content, file_path | 산출물 |
| comments | id, project_id, target_type, target_id, author_id, content | 개인/팀 코멘트 |
| contribution_reports | id, project_id, user_id, summary, evidence | 심사자용 기여도 리포트 |
| evaluation_scores | id, project_id, user_id, score, is_public | 최종 평가 점수 |
| ai_evidence | id, report_id, source_type, source_id, reason | AI 평가 근거 |
| audit_logs | id, user_id, action, target_type, target_id | 접근/수정 이력 |

## 14. API 초안

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | /api/auth/register | 회원가입 |
| POST | /api/auth/login | 로그인 |
| GET/POST | /api/projects | 프로젝트 목록/생성 |
| POST | /api/projects/{id}/members | 팀원/심사자 초대 |
| POST | /api/projects/{id}/meetings | 회의록 업로드 |
| POST | /api/meetings/{id}/summarize | 회의록 AI 요약 |
| GET/POST | /api/projects/{id}/tasks | To-Do 조회/생성 |
| GET | /api/projects/{id}/dashboard | 대시보드 조회 |
| POST | /api/projects/{id}/chat | AI Assistant 질문 |
| POST | /api/projects/{id}/documents | 문서 업로드 |
| POST | /api/projects/{id}/rag/query | 문서 기반 질문 |
| POST | /api/projects/{id}/github | GitHub 저장소 등록 |
| POST | /api/github/{repo_id}/sync | GitHub 데이터 동기화 |
| POST | /api/projects/{id}/deliverables | 산출물 생성 |
| GET | /api/projects/{id}/contribution-reports | 심사자용 기여도 리포트 |
| POST | /api/projects/{id}/evaluation-scores | 최종 평가 점수 입력 |

## 15. 완료 기준

| ID | 완료 기준 |
| --- | --- |
| AC-01 | 사용자는 회원가입/로그인 후 프로젝트를 생성할 수 있다. |
| AC-02 | 팀장, 팀원, 심사자 역할이 구분되고 권한에 따라 접근이 제한된다. |
| AC-03 | 회의록 문서 업로드 후 AI가 요약, 결정사항, 위험요소, To-Do를 생성한다. |
| AC-04 | 생성된 To-Do가 대시보드 진행률에 반영된다. |
| AC-05 | AI Assistant가 회의록, To-Do, 일정, 산출물 관련 질문에 답변한다. |
| AC-06 | 산출물 생성에서 발표자료 또는 보고서 초안이 생성된다. |
| AC-07 | 심사자만 개인별 기여도 리포트와 AI 평가 근거에 접근할 수 있다. |
| AC-08 | 최종 평가 점수는 심사자가 공개 설정한 경우에만 학생에게 표시된다. |
| AC-09 | 데모용 프로젝트 데이터로 중간보고, 2차 보고, 최종보고 시연이 가능하다. |

## 16. 주요 리스크와 대응

| 리스크 | 대응 |
| --- | --- |
| 기능 범위 과다 | P0만 먼저 통합하고 P1/P2는 데모 안정화 후 붙인다. |
| AI 응답 품질 불안정 | 프롬프트 템플릿과 JSON 출력 형식을 고정한다. |
| 일정 부족 | 2주차 말까지 P0 통합본을 만들고 이후는 테스트/보정 중심으로 운영한다. |
| 평가 기능 민감성 | AI는 점수를 확정하지 않고 근거만 제공한다고 명확히 정의한다. |
| 권한 오류 | RBAC 테스트 케이스를 별도로 작성한다. |
| 발표 준비 부족 | 매주 발표용 데모 시나리오와 샘플 데이터를 갱신한다. |
