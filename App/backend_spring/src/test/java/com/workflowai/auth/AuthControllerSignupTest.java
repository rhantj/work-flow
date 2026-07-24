package com.workflowai.auth;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.workflowai.presence.PresenceService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

/**
 * /api/v1/auth/signup의 termsAgreed 필수 검증을 컨트롤러(HTTP) 레벨에서 확인한다.
 * SignupRequest.termsAgreed는 Boolean(래퍼)에 @NotNull + @AssertTrue를 함께 걸어 null(필드
 * 누락)과 false(명시적 거부) 모두 400으로 막는다 — 이 동작이 실제 HTTP 요청/검증 파이프라인
 * (Bean Validation)에서도 그대로 적용되는지는 AuthServiceTest(서비스 단위 테스트)만으로는
 * 보장되지 않는다.
 */
@WebMvcTest(AuthController.class)
@AutoConfigureMockMvc(addFilters = false)
class AuthControllerSignupTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private AuthService authService;

    @MockitoBean
    private GoogleOAuthService googleOAuthService;

    @MockitoBean
    private TestLoginService testLoginService;

    @MockitoBean
    private PresenceService presenceService;

    @Test
    void signup_withoutTermsAgreedField_returns400WithoutCallingService() throws Exception {
        mockMvc.perform(post("/api/v1/auth/signup")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email": "missing@example.com",
                      "password": "12345678",
                      "name": "이름",
                      "roleType": "MEMBER"
                    }
                    """))
            .andExpect(status().isBadRequest());

        verify(authService, never()).signup(
            org.mockito.ArgumentMatchers.any(), org.mockito.ArgumentMatchers.any(),
            org.mockito.ArgumentMatchers.any(), org.mockito.ArgumentMatchers.any(),
            org.mockito.ArgumentMatchers.any()
        );
    }

    @Test
    void signup_withTermsAgreedTrue_succeeds() throws Exception {
        when(authService.signup(eq("new@example.com"), eq("12345678"), eq("이름"), eq("MEMBER"), eq(true)))
            .thenReturn(SignupResponse.active(
                new AuthTokenResponse("access-token", "refresh-token", 1800L, null, null)
            ));

        mockMvc.perform(post("/api/v1/auth/signup")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email": "new@example.com",
                      "password": "12345678",
                      "name": "이름",
                      "roleType": "MEMBER",
                      "termsAgreed": true
                    }
                    """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data.status").value("ACTIVE"));
    }

    @Test
    void signup_withTermsAgreedFalse_explicitlyRejected_returns400WithoutCallingService() throws Exception {
        mockMvc.perform(post("/api/v1/auth/signup")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email": "reject@example.com",
                      "password": "12345678",
                      "name": "이름",
                      "roleType": "MEMBER",
                      "termsAgreed": false
                    }
                    """))
            .andExpect(status().isBadRequest());
    }
}
