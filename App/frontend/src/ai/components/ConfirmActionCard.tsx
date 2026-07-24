import type { ActionCard } from "../libs/types/command";

interface ConfirmActionCardProps {
  card: ActionCard;
  disabled: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmActionCard({ card, disabled, onConfirm, onCancel }: ConfirmActionCardProps) {
  return (
    <section
      aria-label="작업 확인"
      className="rounded-2xl border border-border bg-card p-4 mt-1.5"
    >
      <div className="text-xs font-semibold text-foreground">{card.title}</div>
      <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">{card.summary}</p>
      <div className="flex gap-2 mt-3">
        <button
          type="button"
          onClick={onConfirm}
          disabled={disabled}
          className="flex-1 text-xs font-medium py-2 rounded-lg text-white transition-opacity disabled:opacity-40"
          style={{ background: "linear-gradient(135deg, #3B5BDB 0%, #4F6EF7 100%)" }}
        >
          실행
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={disabled}
          className="flex-1 text-xs font-medium py-2 rounded-lg border border-border text-muted-foreground hover:bg-secondary transition-colors disabled:opacity-40"
        >
          취소
        </button>
      </div>
    </section>
  );
}
