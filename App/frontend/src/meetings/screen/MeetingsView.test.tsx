import { describe, expect, it } from "vitest";
import { buildGeneratedTodos } from "./MeetingsView";
import type { MeetingAiResult } from "../libs/types/meetingAiTypes";

const baseResult = (assignee_id: string | null): MeetingAiResult => ({
  summary: "요약",
  decisions: [],
  risks: [],
  keywords: [],
  meeting_meta: { title: "정기회의", meeting_date: "2026-07-09", participants: ["김민준", "이서연", "박지수", "최동혁"] },
  todos: [
    {
      title: "인증과 권한 구조",
      description: "인증과 권한 구조는 제가 먼저 잡겠습니다.",
      assignee_candidate: "곽진아",
      assignee_id,
      due_date: "2026-07-12",
      priority: "HIGH",
      category: "BACKEND",
      needs_leader_review: assignee_id === null,
    },
  ],
});

describe("buildGeneratedTodos", () => {
  it("leaves the todo unassigned when the server returns a null assignee_id, without defaulting to any member", () => {
    const todos = buildGeneratedTodos(baseResult(null));

    expect(todos[0].assignee).toBe("");
    expect(todos[0].assigned).toBe(false);
  });

  it("trusts the server-provided assignee_id when present, without re-deriving it from assignee_candidate", () => {
    const todos = buildGeneratedTodos(baseResult("3"));

    expect(todos[0].assignee).toBe("3");
    expect(todos[0].assigned).toBe(true);
  });

  it("uses the server-provided evidence_text as the basis when present", () => {
    const result = baseResult(null);
    result.todos[0].evidence_text = "곽진아: 인증과 권한 구조는 제가 먼저 잡겠습니다.";

    const todos = buildGeneratedTodos(result);

    expect(todos[0].basis).toBe("곽진아: 인증과 권한 구조는 제가 먼저 잡겠습니다.");
  });

  it("falls back to a generic basis when evidence_text is missing, without breaking the UI", () => {
    const result = baseResult(null);
    result.todos[0].evidence_text = undefined;

    const todos = buildGeneratedTodos(result);

    expect(todos[0].basis).toBe("회의록 후보 담당자: 곽진아");
  });
});
