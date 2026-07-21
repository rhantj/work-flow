import { useEffect, useState } from "react";
import { X, CheckCircle2, XCircle } from "lucide-react";
import { TaskStatusPill } from "../../board/components/TaskStatusPill";
import { PriorityBadge } from "../../board/components/PriorityBadge";
import { fetchAttendanceDetail, type MeetingAttendanceDetailDto } from "../../meetings/libs/utils/meetingAiApi";
import type { Task, TaskStatus } from "../../board/libs/types/task";

const STATUS_ORDER: TaskStatus[] = ["todo", "inprogress", "blocked", "done"];

interface MemberDrilldownPanelProps {
  mode: "tasks" | "meetings";
  memberName: string;
  memberTasks: Task[];
  projectId: number;
  userId: number;
  onClose: () => void;
}

export function MemberDrilldownPanel({ mode, memberName, memberTasks, projectId, userId, onClose }: MemberDrilldownPanelProps) {
  const [attendance, setAttendance] = useState<MeetingAttendanceDetailDto[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    // 이 패널은 항상 모달 배경(오버레이) 클릭으로만 닫히므로, 열려 있는 동안 다른
    // 멤버/모드로 props가 바뀌는 경우가 없어 stale-response 경합이 발생하지 않는다.
    // 패널이 비모달로 바뀌거나 패널 내 이전/다음 탐색 기능이 추가되면 ignore 플래그가 필요하다.
    if (mode !== "meetings") return;
    setStatus("loading");
    fetchAttendanceDetail(String(projectId), userId)
      .then((result) => {
        setAttendance(result);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, [mode, projectId, userId]);

  const groupedTasks = STATUS_ORDER.map((statusKey) => ({
    statusKey,
    tasks: memberTasks.filter((task) => task.status === statusKey),
  }));

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 w-full max-w-md bg-card border-l border-border shadow-xl z-50 overflow-y-auto">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="text-sm font-bold text-foreground">
            {memberName} · {mode === "tasks" ? "업무 수행 내역" : "회의 참여 내역"}
          </h3>
          <button type="button" onClick={onClose} className="p-1 rounded-md hover:bg-muted">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        {mode === "tasks" ? (
          <div className="p-4 space-y-5">
            {groupedTasks.map(({ statusKey, tasks }) => (
              <div key={statusKey}>
                <div className="flex items-center gap-2 mb-2">
                  <TaskStatusPill status={statusKey} />
                  <span className="text-[11px] text-muted-foreground">{tasks.length}건</span>
                </div>
                {tasks.length === 0 ? (
                  <p className="text-xs text-muted-foreground">해당 상태의 업무가 없습니다.</p>
                ) : (
                  <div className="space-y-2">
                    {tasks.map((task) => (
                      <div key={task.id} className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2">
                        <span className="text-xs font-medium text-foreground truncate">{task.title}</span>
                        <PriorityBadge priority={task.priority} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {memberTasks.length === 0 && (
              <p className="text-xs text-muted-foreground">표시할 업무가 없습니다.</p>
            )}
          </div>
        ) : (
          <div className="p-4">
            {status === "loading" && <p className="text-xs text-muted-foreground">불러오는 중...</p>}
            {status === "error" && <p className="text-xs text-red-600">회의 참여 내역을 불러오지 못했습니다.</p>}
            {status === "ready" && (
              attendance.length === 0 ? (
                <p className="text-xs text-muted-foreground">등록된 회의가 없습니다.</p>
              ) : (
                <div className="space-y-2">
                  {attendance.map((meeting) => (
                    <div key={meeting.meetingId} className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2">
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-foreground truncate">{meeting.title}</div>
                        <div className="text-[11px] text-muted-foreground">{meeting.meetingDate ?? "날짜 미정"}</div>
                      </div>
                      {meeting.attended ? (
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 shrink-0">
                          <CheckCircle2 className="w-3.5 h-3.5" /> 참석
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-red-500 shrink-0">
                          <XCircle className="w-3.5 h-3.5" /> 결석
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
        )}
      </div>
    </>
  );
}
