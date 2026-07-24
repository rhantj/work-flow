package com.workflowai.deliverable;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * 산출물 초안/결과물. 이번 단계에서는 심사자 마이페이지의 제출 현황 카운트 조회에만 쓰인다.
 * 제출/작성 기능(멤버 측) 자체는 이후 단계에서 구현되며, 그때 필드가 추가된다.
 */
@Entity
@Table(name = "deliverables")
public class Deliverable {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "project_id", nullable = false)
    private Long projectId;

    @Column(nullable = false, length = 20)
    private String status;

    protected Deliverable() {
    }

    public Long getId() {
        return id;
    }

    public Long getProjectId() {
        return projectId;
    }

    public String getStatus() {
        return status;
    }
}
