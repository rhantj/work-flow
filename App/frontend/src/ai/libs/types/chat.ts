export interface RagSource {
  // 백엔드(FastAPI RagSource)는 action_item도 반환한다. 여기서 빠뜨리면 타입 가드가
  // 해당 출처를 거부해 저장된 대화 세션이 통째로 폐기된다.
  sourceType: "meeting" | "task" | "action_item";
  sourceId: number;
  contentSnippet: string;
  similarity: number;
}

import type { ActionCard } from "./command";

export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  sources?: RagSource[];
  // 확인 카드가 붙은 어시스턴트 메시지. 실행/취소가 끝나면 undefined로 지워 카드를 감춘다.
  card?: ActionCard;
  // 카드 실행 결과를 그래프에 되돌릴 때 쓰는 그래프 스레드 id. 카드와 짝이다.
  threadId?: string;
}
