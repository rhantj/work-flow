import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import * as meetingAiApi from "../libs/utils/meetingAiApi";
import { MeetingEditPanel } from "./MeetingEditPanel";

describe("MeetingEditPanel", () => {
  it("저장 버튼 클릭 시 triggerAnalysis=false로 버전을 생성한다", async () => {
    const spy = vi.spyOn(meetingAiApi, "createMeetingVersion").mockResolvedValue({ meetingId: "6", status: "SAVED" });
    const onSaved = vi.fn();
    render(<MeetingEditPanel projectId="demo-project" meetingId="5" initialTranscript="원문" onSaved={onSaved} onAnalyzed={vi.fn()} />);

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "수정된 본문" } });
    fireEvent.click(screen.getByText("저장"));

    await Promise.resolve();
    expect(spy).toHaveBeenCalledWith("demo-project", "5", "수정된 본문", false);
    expect(onSaved).toHaveBeenCalled();
  });

  it("분석하기 버튼 클릭 시 triggerAnalysis=true로 버전을 생성한다", async () => {
    const spy = vi.spyOn(meetingAiApi, "createMeetingVersion").mockResolvedValue({ meetingId: "6", status: "PROCESSING" });
    const onAnalyzed = vi.fn();
    render(<MeetingEditPanel projectId="demo-project" meetingId="5" initialTranscript="원문" onSaved={vi.fn()} onAnalyzed={onAnalyzed} />);

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "수정된 본문" } });
    fireEvent.click(screen.getByText("분석하기"));

    await Promise.resolve();
    expect(spy).toHaveBeenCalledWith("demo-project", "5", "수정된 본문", true);
    expect(onAnalyzed).toHaveBeenCalled();
  });
});
