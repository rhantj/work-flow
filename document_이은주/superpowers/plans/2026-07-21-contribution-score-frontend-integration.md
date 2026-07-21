# FS-09 기여도 점수 프론트엔드 연동 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ContributorsView.tsx`의 기여 점수/카테고리 막대를 목업 대신 실제 `/ai/contribution/score`
데이터로 채운다. LLM 서술형 요약(`fetchContributionReport`)·회의 참석
(`fetchAttendanceSummary`)과 나란히, 마지막 남은 숫자 점수 조각을 연동한다.

**Architecture:** `contributorsApi.ts`에 `fetchContributionScore` 함수를 추가하고,
`ContributorsView.tsx`에서 페이지 진입 시 자동 호출(회의 참석 데이터와 동일 패턴)해서
`mergedReports`의 `score`/`categories`를 실데이터로 덮어쓴다. 실패 시 조용히 목업 폴백.
사이드바 카테고리는 실제로 계산되는 3피처(workload/task/meeting)로 축소.

**Tech Stack:** React 19 + TypeScript, Vitest(테스트), 기존 `apiFetch`(envelope 자동 해제).

## Global Constraints

- API 응답 필드명은 snake_case(`assignee_id`, `workload_component`,
  `task_component`, `meeting_component`, `contribution_score`)다 — DTO 변환 시
  camelCase(`assigneeId`, `workloadComponent`, `taskComponent`, `meetingComponent`,
  `contributionScore`)로 정확히 매핑한다.
- `fetchContributionScore`는 `fetchContributionReport`(`App/frontend/src/contributors/libs/utils/contributorsApi.ts`)와
  동일한 형태로 만든다: `apiFetch<T>(path, { method: "POST", body: JSON.stringify({ project_id: projectId }) })`.
  `apiFetch`가 `{success,data,error}` envelope을 이미 벗겨주므로 Raw 타입은 Spring
  `ContributionScoreResponseDto`의 `data` 필드와 그대로 일치시킨다.
- 로딩은 `fetchAttendanceSummary`(`App/frontend/src/meetings/libs/utils/meetingAiApi.ts`)와
  동일하게 `useEffect`로 페이지 진입 시 자동 호출한다 — "새로고침 버튼을 눌러야 갱신"되는
  `fetchContributionReport`(LLM 리포트) 패턴을 따라 하지 않는다.
- 실패 시 조용히 목업으로 폴백한다(`.catch(() => setXxx([]))`) — 에러 배너를 띄우지 않는다
  (`handleRefreshReport`의 `refreshError` 배너 패턴과는 다름).
- 사이드바 카테고리는 정확히 `workload`/`task`/`meeting` 3개만 — `docs`/`dev`/`collab`은
  전부 제거한다(테이블의 "개발" 컬럼 커밋/PR 수는 카테고리 막대와 무관, 그대로 유지).
- 팀원 매칭은 `report.memberId`(문자열) ↔ 응답의 `assigneeId`(문자열) — 별도 변환 없이
  그대로 키로 쓴다.
- 관련 스펙: `document_이은주/superpowers/specs/2026-07-21-contribution-score-frontend-design.md`

---

### Task 1: `fetchContributionScore` API 클라이언트 함수

**Files:**
- Modify: `App/frontend/src/contributors/libs/utils/contributorsApi.ts`
- Test: `App/frontend/src/contributors/libs/utils/contributorsApi.test.ts`

**Interfaces:**
- Produces: `interface ContributionMemberScoreDto { assigneeId: string; workloadComponent: number; taskComponent: number; meetingComponent: number; contributionScore: number }`
- Produces: `interface ContributionScoreResult { members: ContributionMemberScoreDto[]; note: string | null }`
- Produces: `function fetchContributionScore(projectId: number): Promise<ContributionScoreResult>` — Task 2의 `ContributorsView.tsx`가 이 시그니처로 호출
- Consumes: `apiFetch`(`App/frontend/src/global/api/apiClient.ts`, 기존, 수정 없음)

- [ ] **Step 1: 실패하는 테스트부터 작성**

`App/frontend/src/contributors/libs/utils/contributorsApi.test.ts`의 기존 내용 전체를
다음으로 교체(기존 `fetchContributionReport` 테스트는 그대로 유지하고 아래 `describe`
블록만 추가):

```ts
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../global/api/apiClient";
import { fetchContributionReport, fetchContributionScore } from "./contributorsApi";

vi.mock("../../../global/api/apiClient", () => ({
  apiFetch: vi.fn(),
}));

describe("fetchContributionReport", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("converts snake_case response to camelCase", async () => {
    vi.mocked(apiFetch).mockResolvedValue([
      { user_id: 1, name: "김민준", summary: "요약입니다", evidence: ["To-Do 8/10건 완료"] },
    ]);

    const result = await fetchContributionReport(1);

    expect(apiFetch).toHaveBeenCalledWith("/ai/contribution/report", {
      method: "POST",
      body: JSON.stringify({ project_id: 1 }),
    });
    expect(result).toEqual([
      { userId: 1, name: "김민준", summary: "요약입니다", evidence: ["To-Do 8/10건 완료"] },
    ]);
  });
});

describe("fetchContributionScore", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("converts snake_case response to camelCase", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      schema_version: "1.0",
      project_id: 1,
      members: [
        {
          assignee_id: "3",
          workload_component: 100.0,
          task_component: 80.0,
          meeting_component: 80.0,
          contribution_score: 86.7,
        },
      ],
      note: null,
    });

    const result = await fetchContributionScore(1);

    expect(apiFetch).toHaveBeenCalledWith("/ai/contribution/score", {
      method: "POST",
      body: JSON.stringify({ project_id: 1 }),
    });
    expect(result).toEqual({
      members: [
        {
          assigneeId: "3",
          workloadComponent: 100.0,
          taskComponent: 80.0,
          meetingComponent: 80.0,
          contributionScore: 86.7,
        },
      ],
      note: null,
    });
  });

  it("passes through a non-null note", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      schema_version: "1.0",
      project_id: 1,
      members: [],
      note: "배정된 업무가 없어 기여도 점수를 계산할 수 없습니다.",
    });

    const result = await fetchContributionScore(1);

    expect(result).toEqual({
      members: [],
      note: "배정된 업무가 없어 기여도 점수를 계산할 수 없습니다.",
    });
  });
});
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

Run (리포지토리 루트에서): `cd App/frontend && npx vitest run src/contributors/libs/utils/contributorsApi.test.ts`
Expected: FAIL — `fetchContributionScore`가 `contributorsApi.ts`에 없어서
`TypeError: fetchContributionScore is not a function` 또는 import 에러

- [ ] **Step 3: `contributorsApi.ts`에 `fetchContributionScore` 추가**

`App/frontend/src/contributors/libs/utils/contributorsApi.ts`의 기존 내용 전체를
다음으로 교체:

```ts
import { apiFetch } from "../../../global/api/apiClient";

interface RawMemberContribution {
  user_id: number;
  name: string;
  summary: string;
  evidence: string[];
}

export interface MemberContributionDto {
  userId: number;
  name: string;
  summary: string;
  evidence: string[];
}

export async function fetchContributionReport(projectId: number): Promise<MemberContributionDto[]> {
  const data = await apiFetch<RawMemberContribution[]>("/ai/contribution/report", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });

  return data.map((item) => ({
    userId: item.user_id,
    name: item.name,
    summary: item.summary,
    evidence: item.evidence,
  }));
}

interface RawContributionMemberScore {
  assignee_id: string;
  workload_component: number;
  task_component: number;
  meeting_component: number;
  contribution_score: number;
}

interface RawContributionScoreData {
  schema_version: string;
  project_id: number;
  members: RawContributionMemberScore[];
  note: string | null;
}

export interface ContributionMemberScoreDto {
  assigneeId: string;
  workloadComponent: number;
  taskComponent: number;
  meetingComponent: number;
  contributionScore: number;
}

export interface ContributionScoreResult {
  members: ContributionMemberScoreDto[];
  note: string | null;
}

export async function fetchContributionScore(projectId: number): Promise<ContributionScoreResult> {
  const data = await apiFetch<RawContributionScoreData>("/ai/contribution/score", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });

  return {
    members: data.members.map((m) => ({
      assigneeId: m.assignee_id,
      workloadComponent: m.workload_component,
      taskComponent: m.task_component,
      meetingComponent: m.meeting_component,
      contributionScore: m.contribution_score,
    })),
    note: data.note,
  };
}
```

- [ ] **Step 4: 테스트 재실행 → 통과 확인**

Run: `cd App/frontend && npx vitest run src/contributors/libs/utils/contributorsApi.test.ts`
Expected: `3 passed` (기존 `fetchContributionReport` 1개 + 신규 `fetchContributionScore` 2개)

- [ ] **Step 5: 커밋**

```bash
git add App/frontend/src/contributors/libs/utils/contributorsApi.ts \
        App/frontend/src/contributors/libs/utils/contributorsApi.test.ts
git commit -m "feat: fetchContributionScore API 클라이언트 함수 추가"
```

---

### Task 2: `ContributorsView.tsx` 실데이터 연동 + 카테고리 축소

**Files:**
- Modify: `App/frontend/src/global/lib/mock/reviewer.ts`
- Modify: `App/frontend/src/contributors/screen/ContributorsView.tsx`

**Interfaces:**
- Consumes: `fetchContributionScore(projectId: number): Promise<ContributionScoreResult>`,
  `ContributionMemberScoreDto`(둘 다 Task 1에서 정의)

- [ ] **Step 1: 목업 `categories`를 3키로 교체**

`App/frontend/src/global/lib/mock/reviewer.ts`에서 `CONTRIB_REPORTS`의 4개 항목 각각의
`categories:{ ... }` 줄을 다음처럼 정확히 교체(`docs`/`dev`/`collab` 제거, `workload` 추가,
그 외 필드는 전부 그대로 유지):

```ts
// memberId:"1"(김민준) 줄의 categories 교체
    categories:{ task:85, meeting:90, workload:78 } },
```
```ts
// memberId:"2"(이서연) 줄의 categories 교체
    categories:{ task:100, meeting:100, workload:82 } },
```
```ts
// memberId:"3"(박지수) 줄의 categories 교체
    categories:{ task:100, meeting:83, workload:75 } },
```
```ts
// memberId:"4"(최동혁) 줄의 categories 교체
    categories:{ task:33, meeting:67, workload:60 } },
```

- [ ] **Step 2: `ContributorsView.tsx` — import와 타입 수정**

`App/frontend/src/contributors/screen/ContributorsView.tsx`의 30번 줄(기존
`fetchContributionReport` import)을 다음으로 교체(같은 줄에 `fetchContributionScore`와
`ContributionMemberScoreDto`를 추가로 import):

```tsx
import { fetchContributionReport, fetchContributionScore, type MemberContributionDto, type ContributionMemberScoreDto } from "../libs/utils/contributorsApi";
```

35번 줄(`type CategoryKey = keyof (typeof CONTRIB_REPORTS)[number]["categories"];`)을
다음으로 교체 — 목업 파생 타입에서 독립된 고정 타입으로 바꾼다:

```tsx
type CategoryKey = "workload" | "task" | "meeting";
```

43-49번 줄(`CATEGORY_LABELS`)을 다음으로 교체:

```tsx
const CATEGORY_LABELS: Record<CategoryKey, string> = {
  workload: "워크로드",
  task: "업무 수행",
  meeting: "회의 참여",
};
```

- [ ] **Step 3: 자동 로딩 state/effect 추가 + `mergedReports`에 병합**

77번 줄(`}, [currentProjectId]);` — `attendanceSummaries`의 `useEffect` 끝) 바로 다음,
78번 줄(`const attendanceByMemberId = ...`) 바로 앞에 다음을 추가:

```tsx
  // 실제 기여 점수로 목업 score/categories를 보강한다. 실패하면 목업 값을 그대로 쓴다.
  const [contributionScores, setContributionScores] = useState<ContributionMemberScoreDto[]>([]);
  useEffect(() => {
    if (currentProjectId == null) {
      setContributionScores([]);
      return;
    }
    fetchContributionScore(currentProjectId)
      .then((result) => setContributionScores(result.members))
      .catch(() => setContributionScores([]));
  }, [currentProjectId]);
  const contributionByMemberId = useMemo(
    () => Object.fromEntries(contributionScores.map((s) => [s.assigneeId, s])),
    [contributionScores],
  );
```

기존 90-98번 줄의 `mergedReports` 정의 전체를 다음으로 교체:

```tsx
  const mergedReports = useMemo(
    () =>
      CONTRIB_REPORTS.map((report) => {
        const override = reportOverrides[report.memberId];
        const scoreData = contributionByMemberId[report.memberId];
        return {
          ...report,
          aiSummary: override?.summary ?? report.aiSummary,
          evidence: override?.evidence ?? report.evidence,
          score: scoreData ? Math.round(scoreData.contributionScore) : report.score,
          categories: scoreData
            ? { workload: scoreData.workloadComponent, task: scoreData.taskComponent, meeting: scoreData.meetingComponent }
            : report.categories,
        };
      }),
    [reportOverrides, contributionByMemberId],
  );
```

- [ ] **Step 4: 전체 테스트 스위트 회귀 확인**

Run: `cd App/frontend && npm test`
Expected: 기존 전체 통과 + Task 1의 신규 2개 포함, 실패 0건 (이 파일 자체에 대한
컴포넌트 테스트는 기존에도 없으므로 새로 만들지 않음 — 기존 컨벤션과 일치)

- [ ] **Step 5: 개발 서버로 수동 확인**

```bash
cd App/frontend
npm run dev
```

브라우저에서 심사자 데모 로그인 → 기여도 분석 화면 진입. 확인할 것:
- 콘솔에 타입/런타임 에러 없음
- 사이드바 카테고리 막대가 "워크로드"/"업무 수행"/"회의 참여" 3개만 표시됨 (문서 기여/개발
  기여/협업 활동 막대 사라짐)
- 백엔드(`/ai/contribution/score`)가 안 떠 있으면 목업 폴백 값이 정상 표시됨(에러 배너 없이
  조용히 목업 표시) — Docker 스택이 떠 있으면 실제 계산값이 표시됨
- 테이블의 "개발"(커밋/PR) 컬럼은 그대로 목업 값 유지

확인 후 서버 종료(Ctrl+C).

- [ ] **Step 6: 커밋**

```bash
git add App/frontend/src/global/lib/mock/reviewer.ts \
        App/frontend/src/contributors/screen/ContributorsView.tsx
git commit -m "feat: ContributorsView에 기여 점수 실데이터 연동, 카테고리를 workload/task/meeting 3개로 축소"
```

---

## Self-Review 결과 (계획 작성자 자체 점검)

- **스펙 커버리지**: 스펙의 API 클라이언트 함수(Task 1), 자동 로딩 패턴·카테고리 축소·
  목업 폴백·병합 로직(Task 2)이 전부 태스크에 매핑됨. "스코프 밖" 항목(GitHub 카테고리 부활,
  note 배너 노출, evidence 스냅샷 저장)은 의도적으로 태스크에 없음.
- **플레이스홀더**: 없음 — 모든 코드 블록이 실행 가능한 완전한 코드.
- **타입/시그니처 일관성**: `fetchContributionScore(projectId: number) ->
  Promise<ContributionScoreResult>`(Task 1 정의)를 Task 2가 동일 시그니처로 호출.
  `ContributionMemberScoreDto`의 필드명(`assigneeId`/`workloadComponent`/`taskComponent`/
  `meetingComponent`/`contributionScore`)이 Task 1 정의와 Task 2의 병합 코드에서 정확히
  일치. `CategoryKey`(Task 2에서 3개로 재정의)와 `CATEGORY_LABELS`/병합된 `categories`
  객체의 키(`workload`/`task`/`meeting`)가 서로 일치.
- **기존 코드와의 일관성**: `fetchContributionScore`가 `fetchContributionReport`와 동일한
  `apiFetch` 호출 형태, `useEffect` 자동 로딩이 `attendanceSummaries`와 동일한 패턴(같은
  파일의 71-77번 줄), 실패 시 폴백이 `.catch(() => setXxx([]))`로 동일하게 조용함.
