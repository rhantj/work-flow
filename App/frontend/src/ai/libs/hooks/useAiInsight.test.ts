import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { useAiInsight } from "./useAiInsight";
import { apiFetch } from "../../../global/api/apiClient";

vi.mock("../../../global/api/apiClient", () => ({
  apiFetch: vi.fn(),
}));

describe("useAiInsight", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does not ask until ready is true", () => {
    renderHook(() => useAiInsight(1, "질문", false));
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("asks exactly once when ready becomes true, and reports the answer", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ answer: "추천 답변", sources: [] });

    const { result, rerender } = renderHook(
      ({ ready }: { ready: boolean }) => useAiInsight(1, "질문입니다", ready),
      { initialProps: { ready: false } }
    );

    expect(result.current.loading).toBe(false);
    rerender({ ready: true });

    await waitFor(() => expect(result.current.text).toBe("추천 답변"));
    expect(apiFetch).toHaveBeenCalledTimes(1);

    rerender({ ready: true });
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
  });

  it("does not ask when projectId is null", () => {
    renderHook(() => useAiInsight(null, "질문", true));
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("surfaces an error message when the query fails", async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error("일시적으로 답변을 생성할 수 없습니다"));

    const { result } = renderHook(() => useAiInsight(1, "질문", true));

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.text).toBeNull();
  });
});
