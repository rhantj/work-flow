import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { RefreshCw } from "lucide-react";
import { BoardToolbar } from "../components/BoardToolbar";
import { KanbanBoard } from "../components/KanbanBoard";
import { TaskDetailPanel } from "../components/TaskDetailPanel";
import { AddTaskModal } from "../components/AddTaskModal";
import { fetchTasks, updateTaskPosition, deleteTask } from "../libs/utils/taskApi";
import { useStoredComments, addActivity } from "../libs/utils/activityStore";
import { STATUS_LABELS, NEXT_STATUS } from "../libs/utils/taskActions";
import { buildDefaultChecklist, computeInsertPosition } from "../libs/utils/taskService";
import { MEMBERS } from "../../global/lib/mock/members";
import type { Task, TaskStatus } from "../libs/types/task";

const CURRENT_USER = MEMBERS[0];

export function BoardView() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const comments = useStoredComments();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selId, setSelId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [modalStatus, setModalStatus] = useState<TaskStatus>("todo");
  const [toast, setToast] = useState<string | null>(null);

  const selTask = selId ? tasks.find((t) => t.id === selId) ?? null : null;

  const loadTasks = useCallback(() => {
    setLoadState("loading");
    fetchTasks()
      .then((result) => {
        setTasks(result);
        setLoadState("ready");
      })
      .catch(() => setLoadState("error"));
  }, []);

  // 다른 팀원의 변경사항은 실시간으로 반영되지 않고, 이 화면에 새로 들어오거나 새로고침할 때만 반영된다.
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const showToast = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 2200);
  };

  const openModal = (status: TaskStatus) => {
    setModalStatus(status);
    setShowModal(true);
  };

  useEffect(() => {
    if (searchParams.get("openAdd") === "1") {
      openModal("todo");
      const next = new URLSearchParams(searchParams);
      next.delete("openAdd");
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTaskCreated = (task: Task) => {
    setTasks((prev) => [task, ...prev]);
    addActivity(`'${task.title}' 업무를 새로 추가했습니다.`, CURRENT_USER.name, "task-created");
  };

  // 체크리스트/코멘트/활동은 아직 백엔드에 연동되지 않아 이 브라우저에서만 유지된다(후속 작업).
  const patchTaskLocal = (taskId: string, patch: Partial<Task>) => {
    setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, ...patch } : t)));
  };

  // 업무를 targetStatus 컬럼의 insertAtIndex 위치로 옮긴다(같은 컬럼 안 재정렬 + 다른 컬럼으로 이동 모두 이 함수 하나로 처리).
  // tasks 배열은 항상 "표시 순서"(같은 status끼리는 position 오름차순)를 그대로 반영하도록 유지한다.
  const moveTask = async (taskId: string, targetStatus: TaskStatus, insertAtIndex: number) => {
    const dragged = tasks.find((t) => t.id === taskId);
    if (!dragged) return;
    const prevTasks = tasks;

    const withoutDragged = tasks.filter((t) => t.id !== taskId);
    const columnTasks = withoutDragged.filter((t) => t.status === targetStatus);
    const newPosition = computeInsertPosition(columnTasks, insertAtIndex);
    const movedTask = { ...dragged, status: targetStatus, position: newPosition };

    const anchor = columnTasks[insertAtIndex] ?? columnTasks[insertAtIndex - 1];
    const anchorGlobalIndex = anchor ? withoutDragged.indexOf(anchor) : -1;
    const insertGlobalIndex = anchor
      ? (columnTasks[insertAtIndex] ? anchorGlobalIndex : anchorGlobalIndex + 1)
      : withoutDragged.length;

    const next = [...withoutDragged];
    next.splice(insertGlobalIndex, 0, movedTask);
    setTasks(next);

    const statusChanged = dragged.status !== targetStatus;
    try {
      await updateTaskPosition(taskId, targetStatus, newPosition);
      if (statusChanged) {
        addActivity(`'${dragged.title}' 상태를 '${STATUS_LABELS[targetStatus]}'(으)로 변경`, CURRENT_USER.name, "status");
      }
    } catch {
      setTasks(prevTasks);
      showToast("이동에 실패했습니다. 다시 시도해주세요.");
    }
  };

  const handleSelectTask = (id: string) => {
    setSelId((prev) => (prev === id ? null : id));
  };

  const handleToggleChecklistItem = (itemId: string) => {
    if (!selTask) return;
    const checklist = selTask.checklist ?? buildDefaultChecklist(selTask.id, selTask.status);
    const updated = checklist.map((item) => (item.id === itemId ? { ...item, done: !item.done } : item));
    patchTaskLocal(selTask.id, { checklist: updated });
  };

  const handleQuickAction = (label: string, isPrimary: boolean) => {
    if (!selTask) return;
    if (isPrimary) {
      const nextStatus = selTask.status === "done" ? "inprogress" : NEXT_STATUS[selTask.status];
      if (nextStatus) {
        const columnCount = tasks.filter((t) => t.status === nextStatus && t.id !== selTask.id).length;
        moveTask(selTask.id, nextStatus, columnCount);
        showToast(`${label} 완료`);
        return;
      }
    }
    showToast("준비 중인 기능입니다.");
  };

  // 컬럼의 빈 영역에 드롭 = 그 컬럼 맨 끝에 추가.
  const handleDropTask = (taskId: string, status: TaskStatus) => {
    const columnCount = tasks.filter((t) => t.status === status && t.id !== taskId).length;
    moveTask(taskId, status, columnCount);
  };

  const handleDeleteTask = async (taskId: string) => {
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;
    const prevTasks = tasks;
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    setSelId((prev) => (prev === taskId ? null : prev));
    try {
      await deleteTask(taskId);
      addActivity(`'${task.title}' 업무를 삭제했습니다.`, CURRENT_USER.name, "task-deleted");
    } catch {
      setTasks(prevTasks);
      showToast("업무 삭제에 실패했습니다. 다시 시도해주세요.");
    }
  };

  // 카드를 특정 카드의 앞/뒤로 드롭 - 같은 컬럼 안 순서 변경, 다른 컬럼으로 이동 모두 여기로 들어온다.
  const handleReorderTask = (draggedId: string, targetId: string, position: "before" | "after") => {
    if (draggedId === targetId) return;
    const targetTask = tasks.find((t) => t.id === targetId);
    if (!targetTask) return;
    const columnTasks = tasks.filter((t) => t.status === targetTask.status && t.id !== draggedId);
    const targetIndex = columnTasks.findIndex((t) => t.id === targetId);
    if (targetIndex === -1) return;
    const insertAt = position === "after" ? targetIndex + 1 : targetIndex;
    moveTask(draggedId, targetTask.status, insertAt);
  };

  const workspaceMode = Boolean(selTask);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-full flex flex-col overflow-hidden relative" style={{ fontFamily: "'Inter','Noto Sans KR',sans-serif" }}>
        {toast && (
          <div className="fixed top-4 right-6 z-[60] px-4 py-2.5 rounded-xl text-xs font-semibold text-white shadow-lg" style={{ background: "#1C2333" }}>
            {toast}
          </div>
        )}

        <BoardToolbar tasks={tasks} compact={workspaceMode} onAddTask={openModal} />

        <div className="flex-1 overflow-hidden min-h-0">
          {loadState === "loading" && (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">업무를 불러오는 중...</div>
          )}
          {loadState === "error" && (
            <div className="h-full flex flex-col items-center justify-center gap-3 text-sm text-muted-foreground">
              <span>업무를 불러오지 못했습니다.</span>
              <button
                onClick={loadTasks}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white rounded-xl hover:opacity-90 transition-opacity"
                style={{ background: "var(--primary)" }}
              >
                <RefreshCw className="w-3.5 h-3.5" />다시 시도
              </button>
            </div>
          )}
          {loadState === "ready" && (
            workspaceMode && selTask ? (
              <PanelGroup direction="horizontal">
                <Panel defaultSize={68} minSize={40} className="min-w-0">
                  <KanbanBoard
                    tasks={tasks}
                    compact
                    selectedId={selId}
                    onSelectTask={handleSelectTask}
                    onAddTask={openModal}
                    onDropTask={handleDropTask}
                    onReorderTask={handleReorderTask}
                  />
                </Panel>
                <PanelResizeHandle className="group relative w-2.5 shrink-0 flex items-center justify-center outline-none cursor-col-resize">
                  <div className="w-1 h-10 rounded-full bg-border transition-colors group-hover:bg-blue-300 group-active:bg-blue-400" />
                </PanelResizeHandle>
                <Panel defaultSize={32} minSize={24} maxSize={50} className="min-w-0">
                  <TaskDetailPanel
                    task={selTask}
                    comments={comments}
                    onClose={() => setSelId(null)}
                    onQuickAction={handleQuickAction}
                    onToggleChecklistItem={handleToggleChecklistItem}
                    onShowToast={showToast}
                    onDeleteTask={handleDeleteTask}
                  />
                </Panel>
              </PanelGroup>
            ) : (
              <KanbanBoard
                tasks={tasks}
                compact={false}
                selectedId={selId}
                onSelectTask={handleSelectTask}
                onAddTask={openModal}
                onDropTask={handleDropTask}
                onReorderTask={handleReorderTask}
              />
            )
          )}
        </div>

        <AddTaskModal open={showModal} initialStatus={modalStatus} onClose={() => setShowModal(false)} onCreated={handleTaskCreated} />
      </div>
    </DndProvider>
  );
}
