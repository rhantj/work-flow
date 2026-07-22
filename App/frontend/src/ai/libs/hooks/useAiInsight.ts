import { useEffect, useRef } from "react";
import { useRagQuery } from "./useRagQuery";

/** 페이지에 상주하는 "AI 추천 액션" 문구를 RAG 질의로 한 번만 자동 채운다.
 * ready(=페이지 데이터 로딩 완료)가 true가 된 시점에 prompt로 한 번만 질의하고,
 * 이후 prompt가 바뀌어도 다시 묻지 않는다 — 페이지 방문마다 LLM 호출이 반복되는
 * 것을 막기 위함이며, 최신 답변이 필요하면 사용자가 "AI에게 질문" 버튼으로
 * AI 어시스턴트 패널에서 다시 물어볼 수 있다. */
export function useAiInsight(projectId: number | null | undefined, prompt: string, ready: boolean) {
  const { status, answer, error, ask } = useRagQuery();
  const askedRef = useRef(false);

  useEffect(() => {
    if (!ready || projectId == null || askedRef.current) return;
    askedRef.current = true;
    ask(projectId, prompt);
    // prompt/ask는 매 렌더 계산값이라 의존성에 넣지 않는다 — askedRef가 최초 1회만 실행되게 막는다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, projectId]);

  return {
    text: answer?.content ?? null,
    loading: status === "loading" || (ready && projectId != null && !askedRef.current),
    error,
  };
}
