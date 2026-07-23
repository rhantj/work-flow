import { useState } from "react";
import { createMeetingVersion } from "../libs/utils/meetingAiApi";

type MeetingEditPanelProps = {
  projectId: string;
  meetingId: string;
  initialTranscript: string;
  onSaved: () => void;
  onAnalyzed: () => void;
};

export function MeetingEditPanel({ projectId, meetingId, initialTranscript, onSaved, onAnalyzed }: MeetingEditPanelProps) {
  const [transcript, setTranscript] = useState(initialTranscript);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSave = async () => {
    setIsSubmitting(true);
    try {
      await createMeetingVersion(projectId, meetingId, transcript, false);
      onSaved();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnalyze = async () => {
    setIsSubmitting(true);
    try {
      await createMeetingVersion(projectId, meetingId, transcript, true);
      onAnalyzed();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <textarea
        className="w-full min-h-[240px] rounded-lg border border-border bg-card p-3 text-sm text-foreground"
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
      />
      <div className="flex justify-end gap-2">
        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleSave}
          className="px-4 py-2 rounded-lg border border-border bg-card text-sm font-semibold text-foreground hover:bg-muted disabled:opacity-50"
        >
          저장
        </button>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={handleAnalyze}
          className="px-4 py-2 rounded-lg bg-blue-600 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          분석하기
        </button>
      </div>
    </div>
  );
}
