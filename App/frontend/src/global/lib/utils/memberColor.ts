/** 헤더 아바타 + 대시보드 전역 담당자 아바타 칩이 공유하는 단일 색상 배정 소스.
 * 사람마다 서로 다른 색을 갖되, 페이지마다 목록 순서(index)가 달라도 같은 사람은 항상 같은 색이어야 한다.
 * id % 팔레트크기 방식은 id가 팔레트 크기 간격으로 떨어진 두 사람이 같은 색으로 충돌하는 문제가 있었다 —
 * 그래서 "처음 보는 id부터 팔레트를 순서대로 하나씩 배정"하는 방식(assignedColors)으로 바꿔
 * 팀 규모가 팔레트 크기 이하인 한 충돌이 아예 나지 않게 한다. 브라우저 세션 동안 유지된다. */
const MEMBER_COLORS = ["#3B5BDB", "#7048E8", "#10B981", "#F59E0B", "#EF4444", "#06B6D4", "#EC4899", "#84CC16", "#0EA5E9", "#F97316"];
const assignedColors = new Map<string, string>();
let nextColorIndex = 0;

/** 사용자 ID 기준으로 팔레트에서 고정 색을 고른다(최초 등장 순서대로 배정, 이후 항상 동일하게 유지). */
export function stableColorForId(id: string | number | null | undefined): string {
  if (id == null || id === "") return MEMBER_COLORS[0];
  const key = String(id);
  const existing = assignedColors.get(key);
  if (existing) return existing;
  const color = MEMBER_COLORS[nextColorIndex % MEMBER_COLORS.length];
  nextColorIndex += 1;
  assignedColors.set(key, color);
  return color;
}
