import { CATEGORIES, TASKS } from "../mock/tasks";
import type { CategoryDef, ChecklistItem, Task, TaskStatus } from "../types/task";

// 회의록 AI 등 다른 경로로 생성된 업무는 카테고리가 "QA"처럼 대문자일 수 있어 소문자로 맞춰 비교한다.
export function getCat(id: string): CategoryDef {
  const normalized = (id ?? "").toLowerCase();
  return CATEGORIES.find(c => c.id === normalized) ?? CATEGORIES[CATEGORIES.length - 1];
}

// Task.dueDate는 내부적으로 ISO(YYYY-MM-DD)를 쓰고, 화면 표시할 때만 이 함수로 "M.D" 형태로 변환한다.
export function formatDueDate(iso: string): string {
  if (!iso) return "미정";
  const [, month, day] = iso.split("-");
  if (!month || !day) return iso;
  return `${month}.${day}`;
}

const DEFAULT_CHECKLIST_LABELS = ["설계 문서 확인", "구현 완료", "코드 리뷰 완료", "QA 통과"];

export function buildDefaultChecklist(taskId: string, status: TaskStatus): ChecklistItem[] {
  return DEFAULT_CHECKLIST_LABELS.map((label, i) => ({
    id: `${taskId}-CHK-${i}`,
    label,
    done: status === "done" && i < 3,
  }));
}

export function getTasksByStatus(status: TaskStatus, tasks: Task[] = TASKS): Task[] {
  return tasks.filter(t => t.status === status);
}

export function getDoneCount(tasks: Task[] = TASKS): number {
  return tasks.filter(t => t.status === "done").length;
}

export function getProgressPercent(tasks: Task[] = TASKS): number {
  if (tasks.length === 0) return 0;
  return Math.round((getDoneCount(tasks) / tasks.length) * 100);
}

export function getBlockedCount(tasks: Task[] = TASKS): number {
  return tasks.filter(t => t.status === "blocked").length;
}

export function getInProgressCount(tasks: Task[] = TASKS): number {
  return tasks.filter(t => t.status === "inprogress").length;
}

/**
 * 같은 컬럼(status) 안에서 insertAtIndex 위치에 넣을 position 값을 계산한다.
 * columnTasks는 옮겨질 업무를 뺀, 그 컬럼의 현재 표시 순서(position 오름차순)여야 한다.
 * 앞뒤 카드의 position 중간값을 쓰고(Trello 등이 쓰는 표준 기법), 끝에 놓으면 ±1.
 */
export function computeInsertPosition(columnTasks: Task[], insertAtIndex: number): number {
  const prev = columnTasks[insertAtIndex - 1];
  const next = columnTasks[insertAtIndex];
  if (prev && next) return (prev.position + next.position) / 2;
  if (prev) return prev.position + 1;
  if (next) return next.position - 1;
  return 0;
}
