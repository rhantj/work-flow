package com.workflowai.auth;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record SignupRequest(
    @NotBlank(message = "이메일을 입력해주세요.")
    @Email(message = "올바른 이메일 형식으로 입력해주세요.")
    @Size(max = 255, message = "이메일은 255자 이하로 입력해주세요.")
    @Schema(description = "이메일 (로그인 아이디로 사용)", example = "user@example.com")
    String email,

    @NotBlank(message = "비밀번호를 입력해주세요.")
    @Size(min = 8, max = 128, message = "비밀번호는 8자 이상 128자 이하로 입력해주세요.")
    @Schema(description = "비밀번호 (8자 이상)", example = "12345678")
    String password,

    @NotBlank(message = "이름을 입력해주세요.")
    @Size(max = 100, message = "이름은 100자 이하로 입력해주세요.")
    @Schema(description = "이름", example = "홍길동")
    String name,

    @Pattern(regexp = "(?i)^(MEMBER|REVIEWER)$", message = "가입 유형은 MEMBER 또는 REVIEWER만 선택할 수 있습니다.")
    @Schema(description = "가입 유형: MEMBER(일반 회원) 또는 REVIEWER(심사자, 승인 대기)", example = "MEMBER")
    String roleType,

    // Boolean wrapper 타입으로 설정하여 하위 호환성을 확보한다.
    // JSON에 이 필드가 누락되면 null로 바인딩되며, @AssertTrue는 null을 유효한 값(성공)으로 처리한다.
    // 명시적으로 false인 경우에만 회원가입 검증이 실패하여 400 에러를 반환한다.
    @AssertTrue(message = "이용약관 및 개인정보처리방침에 동의해주세요.")
    @Schema(description = "이용약관/개인정보처리방침 동의 여부. 하위 호환성을 위해 null은 허용하며, 명시적으로 false일 때만 가입이 거부됩니다.", example = "true")
    Boolean termsAgreed
) {
}
