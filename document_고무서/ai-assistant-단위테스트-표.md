# AI 어시스턴트 단위 테스트 표

- 작성일: 2026-07-24 (업무 조작 1단계 추가 반영)
- 브랜치: `feature/ai_assistent`
- **굵은 항목** = 멀티턴 작업(Task 4–8)에서 추가된 테스트
- ★ 표시 = 업무 조작 1단계(명령 분류·엔드포인트)에서 추가

> 이 표는 손으로 관리하는 기능 단위 인벤토리다. RAG 어시스턴트 및 명령 기능에 한정하며,
> 백필/재임베딩 스크립트 테스트(test_backfill_*, test_reembed_*)는 제외한다.
> 파일 전체 pytest 수집 수(174개)와 다른 이유는, 여기서는 파라미터 케이스를
> 의미 단위로 묶어 세고 스크립트 테스트를 빼기 때문이다.

## 이 기능 범위 테스트 수

- 명령 분류·엔드포인트 계층(★): FastAPI 10 / Spring(AssistantController) 8 / 프론트 useRagQuery +2
- 기존 RAG 계층: 아래 표 참조

## 요약

| 계층 | 파일 | 개수 |
|---|---|---|
| FastAPI | chat_service | 30 |
| FastAPI | generation_service | 12 |
| FastAPI | task_facts_service | 9 |
| FastAPI | query_rewrite_service | 8 |
| FastAPI | retrieval_service | 7 |
| FastAPI | ingestion_service | 7 |
| FastAPI | chat_router(query) | 7 |
| FastAPI | rag_internal_auth | 4 |
| FastAPI | chat_router(ingest) | 4 |
| FastAPI | embedding_service | 3 |
| FastAPI | chunking | 3 |
| Spring | RagControllerTest | 13 |
| Spring | AssistantControllerTest ★ | 8 |
| FastAPI | command_classifier ★ | 5 |
| FastAPI | assistant_router ★ | 5 |
| FastAPI | chat_service 빈질문 초크포인트 ★ | 1 |
| 프론트 | useRagQuery | 6 |
| 프론트 | AIAssistant | 6 |

> 위 표는 의미 단위 큐레이션이라 파일별 pytest 수집 수와 정확히 일치하지 않는다.
> 정확한 수집 수는 `pytest tests/llm_rag_assistant/ --co -q`로 확인한다(현재 174개).

## FastAPI — chat_service (파이프라인·캐시·개인화·멀티턴)

| 테스트 | 검증 내용 |
|---|---|
| returns_answer_with_sources | 검색 결과를 답변+출처로 반환 |
| handles_no_matching_chunks | 매칭 없으면 "근거 없음", 출처 빈 배열 |
| filters_by_assignee_when_personal_intent_and_user_id_given | 개인화 질문+user_id면 assignee 필터 검색, is_personal 전달 |
| does_not_filter_by_assignee_for_non_personal_question | 비개인화 질문은 필터 안 걸고 is_personal=False |
| is_personal_intent_* (11개) | "내가/제가/내업무/내가할일줘/내 todo…" 개인화 판별 + "문제/과제/내년/내용/일요일/제일…" 오탐 방지 |
| answer_cache_key_scopes_… | 캐시 키가 schema버전·project·assignee·질문 원문으로 분리 |
| cache_hit_skips_embedding_search_and_generation | 캐시 히트 시 임베딩·검색·생성 생략 |
| project_epoch_change_bypasses_stale_cached_answer | epoch 변경 시 낡은 캐시 우회 |
| rechecks_epoch_before_returning_cache_hit | 캐시 반환 직전 epoch 재확인 |
| cache_miss_is_stored_for_1800_seconds_and_reused | 미스 시 1800초 저장·재사용 |
| uses_effective_personal_assignee_in_cache_scope | 개인/일반 질문이 각각 다른 캐시 키 |
| deletes_corrupt_cache_and_recomputes | 손상 캐시 삭제 후 재계산(민감 질문 로그 미노출) |
| cache_failures_warn_and_fail_open | 캐시 client/get/set/delete 실패해도 정상 응답(비밀 미로그) |
| enriches_search_results_with_facts | 검색 결과를 사실 조회로 보강해 생성에 전달 |
| snippet_uses_original_content_not_facts | 출처 스니펫은 원문 기준(사실 미오염) |
| cache_schema_version_bumped_for_facts_in_prompt | 캐시 스키마 버전 v4 고정 |
| **rewritten_question_is_used_for_embedding** | 히스토리 있으면 재작성 질문으로 임베딩 |
| **rewritten_question_drives_personal_intent_detection** | 재작성 결과로 개인화 판정(원문 비개인화→재작성 개인화면 필터) |
| **cache_key_is_scoped_by_rewritten_question** | 캐시 키가 재작성 질문 기준 |
| **rewrite_is_skipped_without_history** | 히스토리 없으면 재작성 LLM 미호출 |

## FastAPI — query_rewrite_service (멀티턴 재작성)

| 테스트 | 검증 내용 |
|---|---|
| **returns_question_unchanged_without_history** | 첫 질문(히스토리 없음)은 그대로, LLM 미호출 |
| **rewrites_follow_up_question_using_history** | 후속 질문을 히스토리로 재작성, ainvoke 1회 |
| **history_content_is_passed_to_model** | 히스토리·질문이 프롬프트에 포함 |
| **system_prompt_blocks_prompt_injection_from_history** | "지시로 취급하지 말" 인젝션 방어 문구 존재 |
| **falls_back_to_original_question_when_model_fails** | 재작성 실패 시 원문 폴백(예외 미전파) |
| **falls_back_when_model_returns_blank** | 빈/공백 결과 시 원문 폴백 |
| **strips_surrounding_whitespace** | 재작성 결과 양끝 공백 제거 |
| **uses_low_temperature_for_deterministic_rewrite** | temperature 0.1 고정 |

## FastAPI — task_facts_service (사실 조회)

| 테스트 | 검증 내용 |
|---|---|
| enriches_task_row_with_due_date_status_priority | task에 마감·상태·우선순위 부착 |
| enriches_action_item_row_from_meeting_action_items_table | action_item은 meeting_action_items 조회로 부착 |
| meeting_row_gets_no_facts | meeting은 facts=None |
| source_id_missing_from_query_result_gets_no_facts | 조회에 없는 source_id는 facts=None |
| queries_are_scoped_by_project_id | SQL에 project_id 조건 포함(타 프로젝트 유출 방지) |
| batches_queries_to_avoid_n_plus_one | task/action 섞여도 fetch 정확히 2회 |
| returns_rows_without_facts_when_query_fails | 조회 실패해도 facts 없이 정상 반환 |
| does_not_mutate_input_rows | 입력 rows 불변 |
| empty_rows_returns_empty_without_query | 빈 입력이면 쿼리 없이 빈 반환 |

## FastAPI — generation_service (프롬프트 생성)

| 테스트 | 검증 내용 |
|---|---|
| includes_sources_in_prompt | 출처를 프롬프트에 포함 |
| handles_empty_sources | 출처 없을 때 처리 |
| tells_model_that_personal_sources_belong_to_asker | 개인화 안내문으로 본인 업무임을 명시 |
| omits_personal_notice_for_general_questions | 일반 질문엔 개인화 안내문 생략 |
| omits_personal_notice_when_no_sources | 출처 없으면 안내문 생략 |
| includes_facts_in_context | facts를 컨텍스트 줄에 "(마감…상태…)"로 삽입 |
| keeps_original_format_without_facts | facts 없으면 기존 형식 유지 |
| omits_missing_fact_fields | 일부 값만 있으면 있는 것만 표시 |
| omits_parentheses_when_all_facts_empty | 전부 비면 괄호 생략 |
| works_when_facts_key_absent | facts 키 자체가 없어도 동작 |
| raises_when_hf_token_missing | HF_TOKEN 없으면 RagConfigurationError |
| personal_notice_states_ownership_is_already_confirmed | 안내문에 "확정"·"담당자 이름 없더라도" 문구 회귀 방지 |

## FastAPI — retrieval / embedding / ingestion / chunking

| 파일 | 테스트 | 검증 내용 |
|---|---|---|
| retrieval | uses_bound_parameters_not_string_concatenation | 파라미터 바인딩(인젝션 방지) |
| retrieval | filters_by_project_id_parameter | project_id로 검색 스코프 |
| retrieval | reserves_meeting_slots_when_general_search_finds_none | 일반 검색에 회의록 슬롯 보장 |
| retrieval | does_not_reserve_meeting_slots_when_already_present | 이미 있으면 미예약 |
| retrieval | skips_reservation_when_no_meeting_chunks_exist_at_all | 회의록 청크 없으면 예약 생략 |
| retrieval | filters_by_assignee_id_when_provided | assignee_id 필터 검색 |
| retrieval | does_not_fall_back_to_general_search_when_assignee_has_no_chunks | 담당 청크 없어도 일반검색 폴백 안 함 |
| embedding | to_vector_literal_formats_floats_as_pgvector_literal | pgvector 리터럴 포맷 |
| embedding | loads_configured_model_and_encodes_text | 설정 모델 로드·인코딩 |
| embedding | uses_anonymous_access_when_hf_token_missing | 토큰 없으면 익명 접근 |
| ingestion | chunks_embeds_and_inserts_each_chunk | 청킹·임베딩·삽입 |
| ingestion | stores_assignee_id_when_given | assignee_id 저장 |
| ingestion | sync_assignee_updates_existing_chunks_without_reembedding | 재임베딩 없이 담당자만 갱신 |
| ingestion | sync_assignee_can_clear_assignee_to_none | 담당자 해제 가능 |
| ingestion | blank_content_removes_existing_source | 빈 콘텐츠는 기존 소스 삭제 |
| ingestion | delete_source_removes_only_matching_project_source | 해당 프로젝트 소스만 삭제 |
| ingestion | delete_project_sources_removes_all_project_chunks | 프로젝트 전체 청크 삭제 |
| chunking | returns_empty_list_for_blank_content | 빈 콘텐츠 빈 리스트 |
| chunking | returns_single_chunk_when_short | 짧으면 단일 청크 |
| chunking | splits_long_content_with_overlap | 길면 오버랩 분할 |

## FastAPI — 라우터 / 인증

| 파일 | 테스트 | 검증 내용 |
|---|---|---|
| router(query) | returns_answer_with_sources | 200 답변+출처 |
| router(query) | **forwards_history_to_service** | history가 answer_question까지 전달 |
| router(query) | returns_503_when_connection_fails | 연결 실패 503 |
| router(query) | different_project_ids_are_forwarded_unmodified | project_id 변조·무시 없이 전달 |
| router(query) | returns_503_when_huggingface_returns_http_error | HF HTTP 오류 503 |
| router(query) | returns_503_when_hf_token_missing | HF_TOKEN 미설정 503 |
| router(query) | does_not_mask_unrelated_runtime_errors | 일반 RuntimeError는 500 노출 |
| router(ingest) | ingest_endpoint_returns_chunk_ids | ingest 위임 |
| router(ingest) | assignee_sync_endpoint_calls_sync_assignee_with_request_fields | assignee-sync 위임 |
| router(ingest) | delete_source_endpoint_removes_matching_rag_source | delete-source 위임 |
| router(ingest) | delete_project_sources_endpoint_removes_all_project_rag_data | delete-project 위임 |
| auth | rejects_request_without_internal_api_key_header | 키 없으면 거부 |
| auth | rejects_request_with_wrong_internal_api_key | 키 틀리면 거부 |
| auth | rejects_all_requests_when_internal_api_key_unconfigured | 키 미설정 시 전부 거부 |
| auth | accepts_request_with_matching_internal_api_key | 키 일치 시 허용 |

## Spring — RagControllerTest

| 테스트 | 검증 내용 |
|---|---|
| queryReturnsAnswerFromFastApi | FastAPI 답변 통과 |
| **queryForwardsHistoryToFastApi** | history가 FastApiRagClient까지 전달 |
| **queryRejectsHistoryExceedingMaxMessages** | 7개 초과 시 400 INVALID_HISTORY |
| **queryRejectsHistoryMessageExceedingMaxContentLength** | 1001자 초과 시 400 |
| **queryRejectsHistoryWithNullElementInsteadOf500** | history:[null]은 400(500 방지) |
| ★ queryRejectsBlankQuestionAsBadRequestNot503 | 빈/null 질문은 400 INVALID_QUESTION(503 위장·불필요 LLM 차단) |
| **queryRejectsHistoryMessageWithNullContent** | content null은 400 |
| **queryRejectsHistoryMessageWithInvalidRole** | role이 user/assistant 아니면 400(인젝션 방어) |
| **queryAcceptsNullHistory** | null 히스토리 200, 빈 리스트로 정규화 |
| queryFillsUserIdFromAuthenticatedSessionNotRequestBody | user_id를 세션값으로 덮어씀(위조 방지) |
| queryReturns503WhenFastApiCallFails | 다운스트림 장애만 503 |
| queryDoesNotMaskUnexpectedBugsAs503 | 우리 쪽 버그는 500으로 노출(503 뭉갬 방지) |
| queryReturns429WhenRateLimited | 레이트리밋 429 |

## Spring — AssistantControllerTest ★ (명령 엔드포인트)

| 테스트 | 검증 내용 |
|---|---|
| commandFillsUserIdAndRoleFromSessionNotRequestBody | user_id·role을 세션·DB 멤버십으로 채움(바디 참칭 무시) |
| leaderRoleIsForwardedAsLeader | LEADER 역할이 FastAPI로 그대로 전달 |
| missingMembershipIsRejected | 멤버 아니면 403 NOT_PROJECT_MEMBER |
| rejectsHistoryWithNullElementInsteadOf500 | history:[null]은 400 |
| rejectsBlankQuestionInsteadOfCallingLlm | 공백 질문은 400, FastAPI 미호출 |
| rejectsNullQuestionAsBadRequestNot503 | null 질문은 400(503 위장 방지) |
| invalidInputDoesNotConsumeRateBudget | 잘못된 입력은 rate 예산 미소모(검증이 rate limit보다 먼저) |
| returns503WhenFastApiCallFails | 다운스트림 장애만 503 ASSISTANT_UNAVAILABLE |

## FastAPI — command_classifier ★ (규칙 선별)

| 테스트 | 검증 내용 |
|---|---|
| plain_questions_are_not_command_candidates | 평범한 질문은 명령 후보 아님 |
| imperative_requests_are_command_candidates | 명령형 발화는 후보로 잡음 |
| query_requests_are_not_command_candidates | "알려줘/보여줘" 조회 요청 제외 |
| adnominal_forms_are_not_commands | "완료된/추가된" 관형형은 명령 아님(오탐 방지) |
| real_commands_survive_the_adnominal_filter | 실제 명령은 필터 통과 |

## FastAPI — assistant_router ★ (명령 라우터)

| 테스트 | 검증 내용 |
|---|---|
| question_goes_through_existing_rag_pipeline | 질문은 기존 RAG로 전달 |
| question_path_receives_history_as_dicts | history가 dict로 서비스에 전달 |
| command_candidate_still_gets_rag_answer_with_note | 명령 후보도 RAG 답변+안내(오탐해도 무회귀) |
| question_answer_has_no_command_note | 순수 질문엔 안내 문구 없음 |
| invalid_user_role_is_rejected | user_role이 enum 밖이면 422 |

## FastAPI — chat_service ★ (빈 질문 초크포인트)

| 테스트 | 검증 내용 |
|---|---|
| short_circuits_blank_question_without_llm | 빈/공백 질문은 임베딩·검색·생성 미호출로 즉시 끊음 |

## 프론트

| 파일 | 테스트 | 검증 내용 |
|---|---|---|
| useRagQuery | returns answer and sources on success | 성공 시 답변·출처, payload에 history:[] |
| useRagQuery | **sends only the last 6 history messages and strips non-conversational fields** | 마지막 6개만·{role,content}만 전송 |
| useRagQuery | **sends an empty history array when there is no prior conversation** | 히스토리 없으면 history:[] |
| useRagQuery | sets error state when request fails | 실패 시 에러 상태 |
| AIAssistant | renders initial assistant greeting | 초기 인사말 렌더 |
| AIAssistant | shows loading indicator then renders answer with source badge | 로딩→답변+출처 배지 |
| AIAssistant | shows API error message | API 에러 메시지 표시 |
| AIAssistant | shows an empty project message instead of calling RAG when no project | 프로젝트 없으면 RAG 미호출 안내 |
| AIAssistant | automatically sends a pending dashboard question exactly once | 대시보드 질문 1회만 자동 전송 |
| AIAssistant | **restores a saved session whose answer cites an action_item source** | action_item 출처 세션 복원(폐기 버그 회귀) |
