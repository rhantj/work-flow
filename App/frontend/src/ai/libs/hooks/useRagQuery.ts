import { useCallback, useRef, useState } from "react";
import { sendCommand, type AssistantHistoryMessage } from "../utils/assistantApi";
import type { RagSource } from "../types/chat";
import type { ActionCard, AssistantResult } from "../types/command";

type RagQueryStatus = "idle" | "loading" | "error" | "success";

interface RagAnswer {
  content: string;
  sources: RagSource[];
  // 명령 경로면 confirm 카드와 그래프 스레드 id가 함께 온다. 질문 경로면 둘 다 없다.
  card: ActionCard | null;
  threadId: AssistantResult["threadId"];
}

export function useRagQuery() {
  const [status, setStatus] = useState<RagQueryStatus>("idle");
  const [answer, setAnswer] = useState<RagAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const ask = useCallback(async (
    projectId: number,
    question: string,
    history: readonly AssistantHistoryMessage[] = [],
  ) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setStatus("loading");
    setError(null);
    try {
      const result = await sendCommand(projectId, question, history, controller.signal);
      if (controller.signal.aborted) return;
      setAnswer({
        content: result.content,
        sources: result.sources,
        card: result.card,
        threadId: result.threadId,
      });
      setStatus("success");
    } catch (err: unknown) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : "일시적으로 답변을 생성할 수 없습니다");
      setStatus("error");
    }
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    setStatus("idle");
  }, []);

  return { status, answer, error, ask, cancel };
}
