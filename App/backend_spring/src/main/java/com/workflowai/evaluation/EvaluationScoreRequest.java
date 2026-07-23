package com.workflowai.evaluation;

import java.math.BigDecimal;

/**
 * 심사자가 팀원 최종 평가 점수를 확정/수정할 때 쓰는 요청.
 * reviewerScore/grade는 학점 계산기에서 입력되며, 공개 토글만 할 때는 null로 보내도 된다
 * (컨트롤러에서 null이면 기존 값을 유지한다).
 */
public record EvaluationScoreRequest(
    Long projectId,
    Long userId,
    BigDecimal score,
    boolean isPublic,
    BigDecimal reviewerScore,
    String grade
) {}
