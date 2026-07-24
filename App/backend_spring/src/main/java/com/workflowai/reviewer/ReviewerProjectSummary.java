package com.workflowai.reviewer;

public record ReviewerProjectSummary(
    Long projectId,
    String title,
    String type,
    String leaderName,
    int memberCount,
    int progressPercent,
    String evalStatus,
    int deliverablesSubmitted,
    int deliverablesTotal,
    boolean githubConnected
) {}
