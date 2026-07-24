import { describe, expect, it, vi, beforeEach } from "vitest";
import { confirmAction } from "./confirmAction";
import { executeAction, type ExecutionResult } from "./actionExecutor";
import { sendResume } from "./assistantApi";
import type { ActionCard, AssistantResult } from "../types/command";

vi.mock("./actionExecutor", () => ({ executeAction: vi.fn() }));
vi.mock("./assistantApi", () => ({ sendResume: vi.fn() }));

function card(overrides: Partial<ActionCard> = {}): ActionCard {
  return {
    stepId: "0-abc",
    tool: "add_comment",
    taskId: 37,
    title: "코멘트 추가",
    summary: "요약",
    args: { content: "확인" },
    ...overrides,
  };
}

const doneAnswer: AssistantResult = {
  type: "done",
  content: "1개 작업을 완료했습니다.",
  sources: [],
  threadId: "t1",
  card: null,
};

describe("confirmAction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("executes then resumes on the happy path and forgets the step", async () => {
    vi.mocked(executeAction).mockResolvedValue({ ok: true });
    vi.mocked(sendResume).mockResolvedValue(doneAnswer);
    const executed = new Map<string, ExecutionResult>();

    const outcome = await confirmAction(card(), "t1", 1, executed);

    expect(outcome).toEqual({ status: "resumed", answer: doneAnswer });
    expect(executed.size).toBe(0);
  });

  it("keeps the successful result when resume fails so a retry does not re-execute", async () => {
    vi.mocked(executeAction).mockResolvedValue({ ok: true });
    vi.mocked(sendResume).mockRejectedValueOnce(new Error("network"));
    const executed = new Map<string, ExecutionResult>();

    const first = await confirmAction(card(), "t1", 1, executed);

    expect(first).toEqual({ status: "resume_failed" });
    expect(executed.get("0-abc")).toEqual({ ok: true });
    expect(executeAction).toHaveBeenCalledTimes(1);

    // 재시도: 재실행 없이 resume만 다시 나가야 한다(add_comment 중복 방지).
    vi.mocked(sendResume).mockResolvedValueOnce(doneAnswer);
    const second = await confirmAction(card(), "t1", 1, executed);

    expect(second).toEqual({ status: "resumed", answer: doneAnswer });
    expect(executeAction).toHaveBeenCalledTimes(1);
    expect(sendResume).toHaveBeenCalledTimes(2);
    expect(executed.size).toBe(0);
  });

  it("does not cache a failed execution so a retry can re-run it", async () => {
    vi.mocked(executeAction).mockResolvedValue({ ok: false, error: "권한 없음" });
    vi.mocked(sendResume).mockResolvedValue(doneAnswer);
    const executed = new Map<string, ExecutionResult>();

    await confirmAction(card(), "t1", 1, executed);

    expect(executed.size).toBe(0);
    // 실패한 실행 결과가 그대로 resume에 실려 그래프가 실패를 인지한다.
    expect(sendResume).toHaveBeenCalledWith(1, "t1", "0-abc", false, "권한 없음");
  });
});
