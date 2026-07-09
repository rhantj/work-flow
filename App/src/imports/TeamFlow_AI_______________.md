# TeamFlow AI 서비스 기획서

## 1. 서비스 개요

TeamFlow AI는 대학생 팀프로젝트, 캡스톤디자인, 해커톤, AI 경진대회, 공모전처럼 제한된 기간 안에 팀이 결과물을 만들어 제출해야 하는 상황을 위한 AI 기반 협업 웹 플랫폼이다.

기존 프로젝트 협업 툴처럼 단순히 업무를 등록하고 관리하는 것에 그치지 않고, 회의록, 일정, To-Do, GitHub 기록, 문서, 산출물, 개인별 기여도 판단 근거까지 하나의 흐름으로 연결한다.

즉 TeamFlow AI는 학생에게는 프로젝트 수행을 돕는 협업 도구이고, 심사자에게는 팀별 진행 상황과 개인별 기여도 근거를 확인할 수 있는 평가 보조 도구이다.

## 2. 서비스 방향 전환

초기 아이디어는 개발 프로젝트 협업 툴에 가까웠다. 하지만 Jira, ClickUp, Notion, Asana 같은 기존 협업 플랫폼이 이미 업무 관리, 대시보드, AI 요약, 자동화 기능을 제공하고 있기 때문에 단순 프로젝트 협업 툴로 가면 차별성이 약해질 수 있다.

따라서 TeamFlow AI는 대상을 대학생 팀프로젝트, 캡스톤, 해커톤, AI 경진대회, 공모전 참가자로 좁히고, 기존에 기획했던 핵심 기능은 유지하되 기여도 분석과 심사자용 평가 보조 기능을 추가한다.

| 구분 | 일반 프로젝트 협업 툴 | TeamFlow AI |
| --- | --- | --- |
| 주요 대상 | 기업, 조직, 실무 프로젝트 팀 | 대학생, 팀프로젝트 팀, 해커톤/경진대회/공모전 참가자 |
| 핵심 목적 | 업무 추적과 조직 운영 | 제한된 기간 안에 산출물을 완성하고 제출 |
| 시작점 | 사용자가 직접 업무 생성 | 회의록/자료/일정에서 AI가 업무와 제출 체크리스트 생성 |
| 산출물 | 보고/문서 작성 보조 | 발표자료, 보고서, 대본, README, 제안서 생성 |
| 평가 기능 | 일반적으로 없음 | 심사자 전용 개인별 기여도 리포트 제공 |
| 차별점 | 기능이 넓고 강력함 | 팀플/공모전/경진대회 흐름에 특화 |

## 3. 주요 사용자

TeamFlow AI의 접근 권한은 크게 팀장, 팀원, 심사자로 구분한다.

| 역할 | 설명 |
| --- | --- |
| 팀장 | 프로젝트 생성, 팀원 초대, 업무 배정, 팀 코멘트 관리, 산출물 관리 |
| 팀원 | 회의록 확인, 개인 업무 수행, 댓글/개인 코멘트 작성, 산출물 공동 작업 |
| 심사자 | 교수, 조교, 심사위원 등. 팀 진행 상황, 개인별 기여도 리포트, AI 평가 근거, 최종 평가 점수 관리 |

심사자는 학생 팀이 볼 수 없는 평가용 데이터를 확인할 수 있다. 특히 개인별 기여도 리포트와 AI 평가 근거는 심사자 전용 정보로 분리한다.

## 4. 핵심 기능 요약

TeamFlow AI는 기존에 기획했던 다섯 가지 기능을 그대로 가져가고, 여기에 기여도 및 평가 보조 기능을 추가한다.

| 기능 | 설명 |
| --- | --- |
| 회의록 AI | 문서, 녹음, 영상 회의 기록을 요약하고 To-Do, 일정, 결정사항, 위험요소로 구조화 |
| AI Assistant | 프로젝트 전체 데이터를 기반으로 질문 답변, 요약, 업무 실행, 산출물 생성 지원 |
| 대시보드 | 진행률, 마감 위험, 담당자별 업무량, 산출물 준비율, GitHub 활동을 시각화 |
| GitHub 관리 | 개발 프로젝트에서 커밋, PR, 이슈, 브랜치 상태를 수집하고 AI가 요약 |
| 산출물 생성 | 발표자료, 보고서, PPT 초안, 대본, README, 제안서, 회고 문서 생성 |
| 기여도 평가 보조 | To-Do, 회의록, GitHub, 문서 기록을 바탕으로 심사자용 개인별 기여도 근거 정리 |

## 5. 회의록 AI

회의록 AI는 TeamFlow AI의 출발점이 되는 기능이다. 팀 회의에서 나온 내용을 사람이 다시 정리하지 않아도 AI가 자동으로 구조화한다.

### 입력 방식

| 입력 | 설명 |
| --- | --- |
| 문서 업로드 | 회의록 PDF, DOCX, TXT 파일 업로드 |
| 녹음파일 업로드 | 음성 파일에서 STT로 텍스트 추출 |
| 영상파일 업로드 | Zoom, Discord 등 화상회의 녹화본에서 음성 추출 후 텍스트 변환 |

### 생성 결과

- 회의 요약
- 핵심 결정사항
- 논의 이슈
- 위험요소
- 그룹 To-Do
- 개인별 To-Do
- 일정 후보
- 다음 회의 아젠다
- 회의록 자동 파일 저장

### 사용 흐름

1. 팀원이 회의록 문서, 녹음파일, 영상파일을 업로드한다.
2. AI가 텍스트를 추출하고 회의 내용을 요약한다.
3. AI가 담당자, 업무, 마감일, 일정, 위험요소를 추출한다.
4. 팀장 또는 팀원이 결과를 검토하고 승인한다.
5. 승인된 업무는 To-Do로 등록되고 일정은 캘린더에 반영된다.
6. 대시보드와 AI Assistant가 해당 데이터를 참고한다.

### 사용 기술

| 기술 | 사용 위치 |
| --- | --- |
| Deep Learning STT | 녹음파일, 영상파일에서 음성을 텍스트로 변환 |
| Whisper 또는 STT API | 음성 인식 모델 |
| FFmpeg | 영상에서 음성 트랙 추출 |
| LLM | 회의 요약, 결정사항 추출, To-Do 생성 |
| NLP/날짜 파싱 | 담당자, 마감일, 일정 후보 추출 |
| Spring Boot API | 파일 업로드 및 회의록 처리 요청 |
| DB | 회의록, 요약 결과, To-Do, 일정 저장 |

## 6. AI Assistant

AI Assistant는 웹서비스 어느 페이지에서도 접근할 수 있는 프로젝트 전용 AI 비서이다. 일반 챗봇이 아니라 현재 프로젝트의 회의록, To-Do, 문서, GitHub 기록, 산출물, 일정 데이터를 우선 참고한다.

### 주요 질문 예시

- "내가 오늘 해야 할 일 알려줘."
- "이번 주 마감 있는 업무 뭐야?"
- "어제 회의에서 결정된 내용만 정리해줘."
- "지금 지연 위험이 있는 기능은 뭐야?"
- "PR #3 내용을 쉽게 설명해줘."
- "발표자료에 넣을 AI 활용 부분 정리해줘."
- "최종 보고서 초안 만들어줘."

### 기능 특징

- 현재 페이지 맥락을 반영한 답변
- 회의록, 문서, To-Do, GitHub, 산출물 근거 표시
- 빠른 질문 버튼 제공
- "To-Do로 만들어줘", "캘린더에 추가해줘" 같은 명령 실행
- 프로젝트별 채팅 이력 저장

### 사용 기술

| 기술 | 사용 위치 |
| --- | --- |
| LLM | 자연어 질문 답변, 요약, 산출물 초안 생성 |
| RAG | 업로드 문서 기반 질문 답변 |
| Embedding | 문서 chunk와 질문을 벡터로 변환 |
| Vector DB | 유사 문서 검색 |
| SQL Query | To-Do, 일정, 회의록, GitHub 데이터 조회 |
| Function Calling/Tool Calling | 캘린더 추가, To-Do 생성 같은 명령 실행 |
| Spring Boot API + Python AI API | 채팅 요청 처리, 프로젝트 데이터 조회, LLM 답변 생성 |

## 7. 대시보드

대시보드는 프로젝트 홈 화면의 중심 기능이다. 팀원과 심사자가 프로젝트 진행 상황을 빠르게 이해할 수 있도록 구성한다.

### 표시 항목

- 전체 진행률
- 오늘 해야 할 일
- 마감 임박 업무
- 지연 위험 업무
- 담당자별 업무량
- 산출물 준비율
- 최근 회의 요약
- 최근 GitHub 활동
- AI 추천 액션
- 블로커 목록

### 진행률 계산 기준

기본 진행률은 To-Do 완료율을 사용한다.

```text
기본 진행률 = 완료된 To-Do 수 / 전체 To-Do 수
```

고도화 단계에서는 우선순위, 마감일, 산출물 준비율, GitHub 활동량, 블로커 수를 함께 반영한다.

### 사용 기술

| 기술 | 사용 위치 |
| --- | --- |
| DB Aggregation | 완료 업무 수, 전체 업무 수, 담당자별 업무량 계산 |
| Rule-based Logic | 마감 임박, 지연, 블로커 조건 판단 |
| Machine Learning 또는 Scoring Model | 업무 지연 위험도, 무임승차 위험 신호 계산 |
| Chart.js/Recharts | 진행률, 업무량, 위험도 시각화 |
| LLM | AI 추천 액션 문장 생성 |
| Spring Boot API | 대시보드 데이터 제공 |

초기 MVP에서는 복잡한 머신러닝 모델보다 점수 기반 Scoring Model을 사용하고, 데이터가 쌓이면 Machine Learning 모델로 고도화한다.

## 8. GitHub 관리

GitHub 관리는 개발 프로젝트, 해커톤, AI 경진대회에서 개발 기록을 프로젝트 데이터로 연결하는 기능이다. 모든 프로젝트에 필수는 아니며, 개발이 포함된 프로젝트에서 선택적으로 사용한다.

### 주요 기능

- GitHub Repository 연결
- 브랜치 상태 조회
- 커밋 기록 수집
- PR 목록 및 상태 조회
- Issue 목록 조회
- AI 커밋/PR 요약
- PR 리뷰 포인트 추천
- 충돌 가능성 표시
- To-Do와 PR/커밋 연결
- GitHub 활동을 기여도 근거로 활용

### 사용 기술

| 기술 | 사용 위치 |
| --- | --- |
| GitHub REST API/GraphQL API | Repository, branch, commit, PR, issue 조회 |
| GitHub Webhook | 새 커밋, PR, issue 발생 시 자동 동기화 |
| LLM | 커밋/PR 내용을 쉬운 말로 요약 |
| Diff 분석 | 변경 파일과 코드 변경량 확인 |
| Rule-based Logic | 오래된 브랜치, 충돌 가능성, 미해결 PR 감지 |
| DB Relation | To-Do와 PR/커밋 연결 |
| Spring Boot API | GitHub 데이터 동기화 및 조회 |

## 9. 산출물 생성

산출물 생성은 TeamFlow AI가 일반 협업툴과 구분되는 핵심 기능이다. 프로젝트 과정에서 쌓인 데이터를 발표자료, 보고서, 제안서, 대본으로 변환한다.

### 생성 가능한 산출물

| 산출물 | 설명 |
| --- | --- |
| 발표자료 초안 | 발표 목차, 슬라이드별 핵심 문장, 발표 대본 생성 |
| 최종 보고서 | 목표, 개발 과정, 결과, 회고 정리 |
| 주간 진행 보고서 | 완료 업무, 지연 업무, 다음 계획 정리 |
| 회의록 정리본 | 회의별 요약과 결정사항을 문서화 |
| GitHub 개발 요약 | 커밋, PR, issue 기반 개발 기록 정리 |
| README 초안 | 프로젝트 소개, 실행 방법, 주요 기능 작성 |
| 공모전 제안서 | 문제 정의, 해결 방안, 기대효과 정리 |
| AI 경진대회 실험 보고서 | 데이터, 모델, 실험 결과, 리더보드 기록 정리 |

### 사용 기술

| 기술 | 사용 위치 |
| --- | --- |
| LLM | 발표자료, 보고서, 대본, 제안서 초안 생성 |
| RAG | 회의록, 문서, GitHub 기록에서 근거 검색 |
| Template Engine | 산출물 유형별 구조 적용 |
| python-pptx 또는 Google Slides API | PPT 파일 생성 확장 |
| ReportLab/DOCX Library | PDF 또는 문서 파일 생성 |
| Spring Boot API + Python AI API | 산출물 생성 요청, LLM 처리, 생성 결과 저장 |

MVP에서는 PPT 파일을 완벽히 자동 생성하기보다 발표 목차, 슬라이드별 내용, 발표 대본, 보고서 초안을 먼저 생성한다.

## 10. 기여도 평가 보조 기능

기여도 평가 보조 기능은 TeamFlow AI의 가장 중요한 차별점이다. AI가 점수를 확정하는 것이 아니라, 심사자가 공정하게 판단할 수 있도록 근거를 정리한다.

### 핵심 원칙

- AI는 최종 점수를 매기지 않는다.
- AI는 개인별 기여도 판단 근거를 정리한다.
- 최종 평가는 심사자가 결정한다.
- 모든 AI 평가 근거에는 출처가 표시되어야 한다.
- 개인별 기여도 리포트와 AI 평가 근거는 심사자만 접근할 수 있다.

### 분석 기준

| 기준 | 데이터 |
| --- | --- |
| 업무 수행 | 배정 To-Do 수, 완료 수, 마감 준수율 |
| 회의 참여 | 회의록 내 담당 언급, 결정사항 참여, 발언 요약 |
| 문서 기여 | 보고서, 발표자료, README, 제안서 작성/수정 기록 |
| 개발 기여 | GitHub 커밋, PR, issue, 코드 리뷰 |
| 협업 활동 | 댓글, 멘션 응답, 블로커 해결 |
| 책임성 | 지연 업무, 재배정 업무, 미완료 업무 |
| 산출물 기여 | 최종 제출물에 반영된 담당 부분 |

### 기여도 리포트 예시

```text
박지수
- 완료 업무: 8개 중 7개
- 주요 담당: 로그인/회원가입, 프로젝트 목록 UI
- GitHub 활동: 커밋 12개, PR 2개
- 문서 기여: 발표자료 UI 흐름 정리 3회
- AI 요약: 프론트엔드 화면 구현과 UI 흐름 정리에 꾸준한 기여가 확인됨.
- 근거: To-Do #3, #8, #11 / PR #4 / 7월 2일 회의록
```

### 사용 기술

| 기술 | 사용 위치 |
| --- | --- |
| DB Aggregation | 개인별 업무 완료 수, 지연 수, 문서 수정 수 집계 |
| GitHub API | 개발 기여 데이터 수집 |
| LLM | 활동 기록을 자연어 기여도 근거로 요약 |
| Machine Learning | 무임승차 위험, 업무 편중, 활동 이상치 탐지 고도화 |
| Rule-based Scoring | MVP 단계에서 기여도 지표 계산 |
| Audit Log | 평가 데이터 접근 및 수정 이력 저장 |

## 11. 접근 제어 및 보안 정책

기여도와 평가 데이터는 민감한 정보이므로 역할 기반 접근 제어가 필요하다. TeamFlow AI는 팀장, 팀원, 심사자 세 가지 역할을 사용한다.

### 권한 정책

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

### 세부 정책

- 회의록, To-Do, 대시보드는 팀장, 팀원, 심사자 모두 접근 가능하다.
- 개인별 기여도 리포트는 심사자만 접근할 수 있다.
- AI 평가 근거는 심사자만 접근할 수 있다.
- 최종 평가 점수는 심사자가 공개로 설정한 경우에만 팀장과 팀원이 확인할 수 있다.
- 개인 코멘트는 모든 역할이 작성할 수 있지만, 공개 범위는 대상자와 작성자, 심사자 중심으로 제한한다.
- 팀 코멘트는 팀장과 심사자가 작성/관리한다.
- 심사자는 초대 코드, 수업 코드, 대회 코드 등을 통해 검증된 사용자만 부여한다.

### 보안 구현 방식

| 보안 요소 | 설명 |
| --- | --- |
| RBAC | 팀장, 팀원, 심사자 역할 기반 권한 검사 |
| Project-level Permission | 사용자가 속한 프로젝트/수업/대회 데이터만 접근 가능 |
| JWT 인증 | 로그인 후 토큰 기반 API 접근 |
| 평가 데이터 분리 | contribution_reports, evaluation_scores, ai_evidence 테이블 분리 |
| 접근 로그 | 심사자 리포트 열람, 점수 수정, 공개 설정 변경 이력 저장 |
| 공개 설정 | 최종 평가 점수 공개 여부를 심사자가 제어 |
| 출처 저장 | AI 평가 근거에 To-Do, 회의록, GitHub PR 등 출처 연결 |

## 12. 전체 기술 스택

| 영역 | 추천 기술 |
| --- | --- |
| Frontend | React 또는 Next.js, TypeScript, Tailwind CSS |
| Backend | Spring Boot, Java, Spring Security, Spring Data JPA 또는 MyBatis |
| AI Backend | Python, Flask 또는 FastAPI, LLM/RAG/STT 처리용 API 서버 |
| Database | MySQL 또는 PostgreSQL |
| Vector DB | Chroma, FAISS, pgvector 중 선택 |
| AI/LLM | OpenAI API 또는 기타 LLM API |
| STT/Deep Learning | Whisper 또는 STT API |
| Machine Learning | 위험도 분석, 기여도 이상치 탐지, 업무 편중 분석 |
| File Processing | pdfplumber, python-docx, FFmpeg |
| GitHub 연동 | GitHub REST API, GraphQL API, Webhook |
| Background Jobs | Celery 또는 RQ, Redis |
| Storage | 로컬 파일 저장, AWS S3, Cloud Storage |
| Visualization | Chart.js, Recharts |
| Auth/Security | Spring Security, JWT, RBAC, 접근 로그 |
| PDF/PPT 생성 | ReportLab, python-pptx, Google Slides API |

## 13. AI 기술 사용 위치 정리

| AI 기술 | 사용 기능 |
| --- | --- |
| LLM | 회의 요약, To-Do 추출, AI Assistant 답변, GitHub 요약, 산출물 생성, 기여도 근거 요약 |
| RAG | 문서 Q&A, 프로젝트 자료 기반 답변, 산출물 근거 검색 |
| Embedding | 문서 chunk와 질문을 벡터로 변환 |
| Deep Learning | STT, 음성 인식, 임베딩 모델, 추후 영상/자막 분석 |
| Machine Learning | 지연 위험도 예측, 업무 편중 분석, 무임승차 위험 신호 탐지 |
| Rule-based Logic | 마감 임박 판단, 점수 기반 위험도 계산, 권한 조건 처리 |

## 14. 데이터 모델 초안

| 테이블 | 주요 필드 | 용도 |
| --- | --- | --- |
| users | id, email, password_hash, name, role | 사용자 |
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
| contribution_reports | id, project_id, user_id, summary, evidence, created_at | 심사자용 기여도 리포트 |
| evaluation_scores | id, project_id, user_id, score, is_public | 최종 평가 점수 |
| ai_evidence | id, report_id, source_type, source_id, reason | AI 평가 근거 |
| audit_logs | id, user_id, action, target_type, target_id, created_at | 접근/수정 이력 |

## 15. MVP 범위

### P0

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

### P1

- 녹음파일 STT
- 영상파일 음성 추출
- GitHub Repository 연동
- GitHub 커밋/PR/issue 요약
- 문서 RAG Q&A
- 댓글/개인 코멘트/팀 코멘트
- 최종 평가 점수 공개 설정
- AI 평가 근거 출처 표시

### P2

- PPT/PDF 자동 다운로드
- AI 경진대회 실험 로그 관리
- 리더보드 기록 관리
- 고도화된 Machine Learning 기여도 분석
- 화면 OCR 기반 영상 분석
- 외부 캘린더 연동

## 16. 최종 포지셔닝 문장

TeamFlow AI는 대학생 팀프로젝트, 캡스톤, 해커톤, AI 경진대회, 공모전처럼 제한된 기간 안에 팀이 결과물을 제출해야 하는 상황에서 회의록, 업무, 일정, 개발/실험 기록, 산출물, 개인별 기여도 평가 근거를 AI가 연결해주는 협업 및 평가 보조 플랫폼이다.

기존 협업툴이 업무 관리에 집중한다면, TeamFlow AI는 팀이 프로젝트를 끝까지 완성하고 제출하며, 심사자가 과정과 기여도를 공정하게 확인할 수 있도록 돕는 데 집중한다.
