import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AIAssistant } from "./AIAssistant";
import { apiFetch } from "../../global/api/apiClient";

vi.mock("../../global/hooks/useAuth", () => ({
  useAuth: () => ({ currentProjectId: 1 }),
}));

vi.mock("../../global/api/apiClient", () => ({
  apiFetch: vi.fn(),
}));

describe("AIAssistant", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders initial assistant greeting", () => {
    render(<AIAssistant onClose={() => {}} />);
    expect(screen.getByText(/WorkFlow AI 어시스턴트/)).toBeInTheDocument();
  });

  it("shows loading indicator then renders answer with source badge", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      answer: "실제 RAG 답변",
      sources: [{ source_type: "meeting", source_id: 3, content_snippet: "요약", similarity: 0.8 }],
    });

    render(<AIAssistant onClose={() => {}} />);
    const textbox = screen.getByPlaceholderText("프로젝트에 대해 무엇이든 물어보세요...");
    await userEvent.type(textbox, "오늘 할 일 알려줘");
    await userEvent.click(screen.getByRole("button", { name: "전송" }));

    await waitFor(() => expect(screen.getByText("실제 RAG 답변")).toBeInTheDocument());
    expect(screen.getByText(/출처: 회의록 #3/)).toBeInTheDocument();
  });

  it("shows API error message", async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error("로그인이 필요합니다."));

    render(<AIAssistant onClose={() => {}} />);
    const textbox = screen.getByPlaceholderText("프로젝트에 대해 무엇이든 물어보세요...");
    await userEvent.type(textbox, "질문{enter}");

    await waitFor(() => expect(screen.getByText("로그인이 필요합니다.")).toBeInTheDocument());
  });
});
