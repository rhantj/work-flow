package com.workflowai.meeting;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class MeetingTest {

    private Meeting newOriginal() {
        return new Meeting(1L, "정기회의", "document", null, "completed", LocalDate.now(), "정기회의", "a.txt", 10L, 100L);
    }

    @Test
    void originalMeetingHasNullVersioningFields() {
        Meeting meeting = newOriginal();
        assertThat(meeting.getOriginalMeetingId()).isNull();
        assertThat(meeting.getEditedBy()).isNull();
        assertThat(meeting.getSavedAt()).isNull();
    }

    @Test
    void markSavedSetsSavedAtOnce() {
        Meeting meeting = newOriginal();
        meeting.markSaved();
        assertThat(meeting.getSavedAt()).isNotNull();
    }

    @Test
    void newVersionCopiesTranscriptAndLinksToOriginal() {
        Meeting original = newOriginal();
        Meeting version = Meeting.newVersion(original, "수정된 본문", 20L, "정기회의_수정본");

        assertThat(version.getOriginalMeetingId()).isEqualTo(original.getId());
        assertThat(version.getEditedBy()).isEqualTo(20L);
        assertThat(version.getTitle()).isEqualTo("정기회의_수정본");
        assertThat(version.getTranscript()).isEqualTo("수정된 본문");
        assertThat(version.getAnalysisStatus()).isEqualTo("pending");
        assertThat(version.getProjectId()).isEqualTo(original.getProjectId());
    }
}
