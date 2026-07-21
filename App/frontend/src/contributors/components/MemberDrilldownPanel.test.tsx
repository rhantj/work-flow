import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { MemberDrilldownPanel } from "./MemberDrilldownPanel";
import { fetchAttendanceDetail } from "../../meetings/libs/utils/meetingAiApi";
import type { Task } from "../../board/libs/types/task";

vi.mock("../../meetings/libs/utils/meetingAiApi", () => ({
  fetchAttendanceDetail: vi.fn(),
}));

function makeTask(id: string, title: string, status: Task["status"]): Task {
  return { id, title, status, priority: "medium", assignee: "1", dueDate: "", labels: [], category: "backend", position: 0 };
}

describe("MemberDrilldownPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("groups tasks by status in tasks mode", () => {
    const tasks = [
      makeTask("A", "AI 모델 학습 파이프라인 구축", "done"),
      makeTask("B", "데이터 전처리 스크립트 작성", "inprogress"),
    ];

    render(
      <MemberDrilldownPanel
        mode="tasks"
        memberName="김민준"
        memberTasks={tasks}
        projectId={1}
        userId={1}
        onClose={() => {}}
      />
    );

    expect(screen.getByText("AI 모델 학습 파이프라인 구축")).toBeInTheDocument();
    expect(screen.getByText("데이터 전처리 스크립트 작성")).toBeInTheDocument();
  });

  it("fetches and shows attendance detail in meetings mode", async () => {
    vi.mocked(fetchAttendanceDetail).mockResolvedValue([
      { meetingId: "12", title: "12.10 팀 정기 회의", meetingDate: "2026-12-10", attended: true },
      { meetingId: "15", title: "12.11 스프린트 리뷰", meetingDate: "2026-12-11", attended: false },
    ]);

    render(
      <MemberDrilldownPanel
        mode="meetings"
        memberName="김민준"
        memberTasks={[]}
        projectId={1}
        userId={1}
        onClose={() => {}}
      />
    );

    await waitFor(() => expect(screen.getByText("12.10 팀 정기 회의")).toBeInTheDocument());
    expect(screen.getByText("12.11 스프린트 리뷰")).toBeInTheDocument();
    expect(fetchAttendanceDetail).toHaveBeenCalledWith("1", 1);
  });
});
