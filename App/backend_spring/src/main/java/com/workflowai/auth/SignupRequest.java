package com.workflowai.auth;

import io.swagger.v3.oas.annotations.media.Schema;

public record SignupRequest(
    @Schema(description = "이메일 (로그인 아이디로 사용)", example = "user@example.com") String email,
    @Schema(description = "비밀번호 (8자 이상)", example = "12345678") String password,
    @Schema(description = "이름", example = "홍길동") String name,
    @Schema(description = "가입 유형: MEMBER(일반 회원) 또는 REVIEWER(심사자, 승인 대기)", example = "MEMBER") String roleType
) {
}
