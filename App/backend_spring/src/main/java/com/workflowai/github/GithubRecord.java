package com.workflowai.github;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * GitHub 커밋/PR/Issue 동기화 기록. 이번 단계에서는 심사자 마이페이지의
 * "GitHub 연동 여부" 표시에만 쓰인다. 실제 동기화 기능은 아직 없어 항상 0건이다.
 */
@Entity
@Table(name = "github_records")
public class GithubRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "project_id", nullable = false)
    private Long projectId;

    protected GithubRecord() {
    }

    public Long getId() {
        return id;
    }

    public Long getProjectId() {
        return projectId;
    }
}
