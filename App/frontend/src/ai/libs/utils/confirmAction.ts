import { executeAction, type ExecutionResult } from "./actionExecutor";
import { sendResume } from "./assistantApi";
import type { ActionCard, AssistantResult } from "../types/command";

export type ConfirmOutcome =
  | { status: "resumed"; answer: AssistantResult }
  // 쓰기는 됐으나 결과 전달(resume)이 실패했다. 재실행 없이 다시 시도할 수 있다.
  | { status: "resume_failed" };

/**
 * 확인 카드를 실행하고 그 결과를 그래프에 되돌린다.
 *
 * 쓰기(executeAction)와 결과 전달(sendResume)은 실패 의미가 다르다.
 * - 쓰기 실패: DB에 변화가 없으니 다시 눌러 재실행해도 안전하다.
 * - 쓰기 성공 후 resume 실패: DB는 이미 바뀌었으니 재실행하면 add_comment 등이 중복된다.
 *   그래서 성공한 실행 결과를 stepId로 기억해 두고, 재시도 시 resume만 다시 보낸다.
 *
 * @param executed stepId → 성공했지만 아직 resume되지 않은 실행 결과. 호출부가 소유하고
 *   재시도 사이에 유지한다. resume 성공 시 여기서 제거된다.
 */
export async function confirmAction(
  card: ActionCard,
  threadId: string,
  projectId: number,
  executed: Map<string, ExecutionResult>
): Promise<ConfirmOutcome> {
  let result = executed.get(card.stepId);
  if (!result) {
    result = await executeAction(card, projectId);
    // 성공한 쓰기만 기억한다. 실패는 부작용이 없어 재시도 시 다시 실행해도 안전하다.
    if (result.ok) executed.set(card.stepId, result);
  }

  try {
    const answer = await sendResume(projectId, threadId, card.stepId, result.ok, result.error);
    executed.delete(card.stepId);
    return { status: "resumed", answer };
  } catch {
    return { status: "resume_failed" };
  }
}
