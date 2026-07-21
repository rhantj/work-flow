package com.workflowai.auth;

import io.swagger.v3.oas.annotations.media.Schema;

public record LoginRequest(
    @Schema(description = "이메일", example = "user@example.com") String email,
    @Schema(description = "비밀번호", example = "12345678") String password
) {
}
