# 어시스턴트 답변 품질 베이스라인 (2026-08-19)

`docs/notebooks/assistant-eval/04_assistant_eval_baseline.ipynb` 를 끝까지 실행해 얻은 실측이다.
이 문서의 숫자는 전부 그 실행에서 나왔고, 원자료는 `output/assistant_eval/data/runs_20260819.csv`
(90행 = 3모드 x 30문항)에 있다.

## 측정 조건

| 항목 | 값 |
|---|---|
| 평가셋 | `App/backend_fastapi/tests/fixtures/assistant_eval/` 30건 (identifier 10 / semantic 10 / mixed 10) |
| 대상 프로젝트 | `project_id = 1` |
| 진입점 | `chat_service.answer_question` (운영과 같은 검색·컨텍스트·프롬프트 경로) |
| 근거 채점기 | `tests/assistant_eval/scorer.py` (LLM 불필요, 결정적) |
| 충실도·안전성 심사기 | `tests/assistant_eval/judge.py` + Qwen/Qwen3-4B-Instruct-2507 (HF router) |
| 측정 모드 | `huggingface`, `ollama`, `auto` |
| 실패한 측정 | 0건 |
| 심사기 판정 불가(`unparsed`) | 0문항 (심사기 원응답은 `예`/`아니오` 두 가지뿐) |
| 캐시 응답 | 0건 (모드마다 `advance_rag_project_epoch(1)` 로 무효화 후 측정) |

`gemini` 는 측정하지 않았다. `.env` 에 `GEMINI_API_KEY` 가 없어
`RagConfigurationError: GEMINI_API_KEY is not configured.` 로 프로브 단계에서 걸렀다.
설정 부재를 0점으로 표에 넣으면 품질 저하로 오독되기 때문에 열 자체를 뺐다.

## 백엔드별 점수 (30문항 평균)

| 모드 | 실제 응답 백엔드 | grounding | coverage | safety | faithfulness | 평균 소요 |
|---|---|---|---|---|---|---|
| `huggingface` | huggingface 30/30 | 0.783 | 0.478 | 0.833 | 0.361 | 8.1s |
| `ollama` | ollama 30/30 | 0.783 | 0.478 | 0.900 | 0.428 | 16.6s |
| `auto` | huggingface 30/30 | 0.783 | 0.494 | 0.833 | 0.378 | 8.0s |

`faithfulness = coverage x safety` 다(평균이 아니라 곱인 이유는 `judge.py` docstring).
> **채점기 정정 (2026-08-20).** 아래 표의 `grounding` 은 **id 전용 채점**으로 낸 값이다.
> 그 뒤 채점기가 같은 문장을 담은 중복 청크를 근거로 인정하도록 고쳐졌고(본문 대조 합집합),
> 노트북 호출부도 본문을 넘기도록 연결했다. 같은 검색 결과에 새 채점기를 적용하면:
>
> | 분류 | 표의 값(id 전용) | 새 채점기 | 차이 |
> |---|---|---|---|
> | identifier | 1.000 | 1.000 | +0.000 |
> | mixed | 0.950 | 0.950 | +0.000 |
> | semantic | 0.400 | 0.433 | +0.033 |
> | **전체** | **0.783** | **0.794** | **+0.011** |
>
> 바뀐 케이스는 `semantic-09` 하나다(검색기가 화이트리스트의 `task#77` 대신 같은 문장을
> 담은 `task#35` 를 올렸다). **차이가 작다는 것이 요점이다 — semantic 0.40 의 대부분은
> 채점 결함이 아니라 진짜 검색 실패다.**
>
> 노트북을 다시 돌리지 않고 이 표를 고칠 수 있는 이유: 검색은 결정적이라 재실행 없이도
> 같은 결과가 나온다. 실제로 id 전용으로 다시 계산해 아래 표의 값을 소수 셋째 자리까지
> 그대로 재현한 뒤 새 채점기를 적용했다. `coverage`·`safety`·`faithfulness` 는 이 변경과
> 무관하므로 손대지 않았다. 노트북에 남은 실행 출력도 정정 이전 값이다.

`grounding` 은 세 모드가 소수 셋째 자리까지 같다 — 검색이 결정적으로 돌고 있다는 뜻이고,
생성 백엔드를 바꿔도 움직이지 않아야 정상인 축이 실제로 안 움직였다.

`auto` 는 30건 전부 HuggingFace 가 답했다. 폴백이 한 번도 발동하지 않았으므로 `auto` 열은
사실상 `huggingface` 열의 재측정이다. 두 열의 차이는 `semantic-05` 한 건뿐이고
(faithfulness 0.0 -> 0.5), 이 차이는 백엔드 차이가 아니라 생성·심사의 비결정성이다.
**모드 간 0.05 이하 차이는 유의미하지 않다**는 잡음 하한을 이 한 건이 알려준다.

## 분류 x 백엔드

| 분류 | 모드 | grounding | coverage | safety | faithfulness |
|---|---|---|---|---|---|
| identifier | huggingface | 1.00 | 0.800 | 0.60 | 0.500 |
| identifier | ollama | 1.00 | 0.600 | 0.85 | 0.550 |
| identifier | auto | 1.00 | 0.800 | 0.60 | 0.500 |
| mixed | huggingface | 0.95 | 0.450 | 0.90 | 0.400 |
| mixed | ollama | 0.95 | 0.550 | 0.85 | 0.450 |
| mixed | auto | 0.95 | 0.450 | 0.90 | 0.400 |
| semantic | huggingface | 0.40 | 0.183 | 1.00 | 0.183 |
| semantic | ollama | 0.40 | 0.283 | 1.00 | 0.283 |
| semantic | auto | 0.40 | 0.233 | 1.00 | 0.233 |

## 이 표에서 읽히는 것

**1. 병목은 생성이 아니라 semantic 검색이다.**
identifier 는 grounding 1.00, mixed 0.95 인데 semantic 만 0.40 이다. semantic 10건 중
`semantic-03`·`semantic-08`·`semantic-09` 는 0.00, `semantic-02`·`semantic-06` 은 0.33 이다.
식별자(WF-xxx)가 없는 질문에서 그 사실을 품은 청크가 상위 5건에 아예 못 올라온다는 뜻이고,
프롬프트를 어떻게 고쳐도 없는 근거로 답할 수는 없다. semantic 의 coverage 상한이 곧
grounding(0.40)이라는 것이 표에도 그대로 보인다.

**2. 두 백엔드가 반대 방향으로 실패한다.**
- HuggingFace 는 컨텍스트 메타데이터를 그대로 옮겨 적는다. 예를 들어 `identifier-02` 답변은
  `FS-3 대시보드/지연 위험도 - [Jira01 재검증 테스트 삽입] WF-195 (담당자: <실명>,
  마감: <날짜>, 상태: done, 우선순위: high)` 였다(인명·날짜는 가렸다 - 원자료는
  `data/` 에 있고 추적하지 않는다). 사실은 담겼으니 coverage 0.800 이지만,
  `must_not_claim` 의 "담당자를 특정한다"·"마감일을 특정한다"에 걸려 safety 0.60 으로 깎인다.
- Ollama 는 반대로 너무 짧다. 같은 문항 답변이 `WF-195` 한 줄이다. 안전성은 0.85 로 높지만
  identifier coverage 가 0.600 까지 떨어진다.

즉 identifier 구간의 낮은 점수는 대부분 **모델이 틀렸기 때문이 아니라 답변 분량 정책이 없기
때문**이다. `task_facts_service.enrich_with_facts` 가 컨텍스트에 붙이는 마감일·담당자를
그대로 되뱉을지 말지를 프롬프트가 정해주지 않고 있다.

**3. semantic 의 safety 1.00 은 좋은 신호가 아니다.**
근거가 안 올라온 질문에 대해 답이 아무것도 특정하지 않았다는 뜻이다. coverage 0.183~0.283 과
같이 읽어야 한다. `faithfulness` 가 곱인 이유가 여기서 드러난다 — 평균이었으면 semantic 이
0.59 로 가장 높은 분류가 됐을 것이다.

## 그래프

`output/assistant_eval/figures/`

| 파일 | 내용 |
|---|---|
| `provider_scores.png` | 백엔드별 4개 축 평균 막대 |
| `category_heatmap.png` | 분류 x 백엔드 faithfulness 히트맵 |
| `progress.png` | 실행 순서에 따른 누적 평균 faithfulness · 누적 소요 시간 (진행 상황) |
| `per_case_scores.png` | 케이스별 faithfulness 와 grounding |

## 측정 한계

이 숫자를 다른 용도로 쓰기 전에 반드시 읽는다.

1. **합성 평가셋 30건이다.** 분류당 10건이라 분류별 평균 한 칸이 문항 1건에 0.1 씩 움직인다.
   절대값에 통계적 의미를 두지 말고 before/after 차이로만 쓴다.
2. **모드 간 0.05 이하 차이는 잡음이다.** 같은 백엔드를 두 번 잰 `huggingface`/`auto` 열이
   coverage 0.478 vs 0.494 로 갈렸다. 이 폭 안의 개선은 개선이라고 부르지 않는다.
3. **`huggingface`/`auto` 열의 충실도·안전성은 자기평가다.** 심사 모델(Qwen3-4B)이 HF 생성
   티어와 같은 모델이다. 회의록 하네스(`03`)가 같은 이유로 같은 선택을 했고, 두 하네스를
   비교하려면 조건을 맞춰야 해서 그대로 뒀다. `ollama` 열만 심사자와 피심사자가 다르다.
4. **`gemini` 는 재지 못했다.** 키가 없다. 운영에서 HF 가 죽으면 실제로 타는 경로인데
   품질을 모른다. `GEMINI_API_KEY` 를 넣고 노트북을 다시 돌리면 열이 하나 더 생긴다.
5. **폴백 경로를 실측하지 못했다.** `auto` 30건이 전부 HF 로 답해서, HF 장애 시 품질이
   어떻게 되는지는 이 표에 없다.
6. **grounding 은 "답변이 인용했는가"가 아니다.** "그 사실을 품은 출처가 검색에 올라왔는가"다.
   운영 프롬프트가 인용 표기를 요구하지 않아 답변에서 출처를 파싱할 수 없기 때문이며, 근거
   전문은 `scorer.py` docstring 에 있다. 사실상 검색기 품질 지표로 읽어야 한다.
7. **`off_whitelist_sources` 평균 3.6 은 결함이 아니다.** 검색기가 항상 5건을 올리는데
   케이스별 화이트리스트는 1~5건이라 남는 것이 잡히는 값이다. 점수식에는 들어가지 않는
   진단값이다(같은 실패를 두 번 세지 않으려고 `scorer.py` 가 일부러 뺐다).
8. **답변 캐시는 껐지만 검색 캐시는 그대로다.** 모드마다 `advance_rag_project_epoch(1)` 로
   답변 캐시를 무효화했다. 그래서 `provider="cache"` 는 0건이다. 검색 계층 캐시까지
   무효화하지는 않았으므로, 세 모드의 grounding 이 완전히 동일한 데에는 그 효과도 섞여 있다.
9. **한 시점 1회 측정이다.** 반복 측정으로 분산을 구하지 않았다. 3번의 잡음 폭도 1회
   비교에서 나온 하한이지 표준편차가 아니다.
10. **원자료 CSV 는 저장소에 넣지 않았다.** `answer` 열에 프로젝트 1번의 실제 업무·회의록
    내용이 그대로 들어 있다. `output/assistant_eval/data/` 는 추적하지 않고 로컬에만 둔다.

## 다음에 무엇을 잴 것인가

- semantic 검색 개선(#621/#622 계열)은 **grounding semantic 0.40** 을 기준선으로 삼는다.
  이 값이 안 오르면 coverage 도 안 오른다.
- 프롬프트에 답변 분량·메타데이터 노출 규칙을 넣는 작업은 **identifier safety 0.60(HF)** 과
  **identifier coverage 0.600(Ollama)** 을 동시에 본다. 한쪽만 보면 다른 쪽을 깎는다.
- 재측정은 같은 노트북을 그대로 돌린다. `ASSISTANT_EVAL_ENV_FILE` 로 `App/.env` 경로를 주면
  워크트리에서도 돈다.
