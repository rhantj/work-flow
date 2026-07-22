package com.workflowai.auth;

import com.workflowai.security.JwtService;
import com.workflowai.user.User;
import com.workflowai.user.UserRepository;
import io.jsonwebtoken.Claims;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {
    private static final String PROVIDER_GOOGLE = "google";
    private static final String PROVIDER_DEMO = "demo";
    private static final String PROVIDER_LOCAL = "local";

    private final GoogleOAuthService googleOAuthService;
    private final UserRepository userRepository;
    private final JwtService jwtService;
    private final PasswordEncoder passwordEncoder;

    public AuthService(
        GoogleOAuthService googleOAuthService,
        UserRepository userRepository,
        JwtService jwtService,
        PasswordEncoder passwordEncoder
    ) {
        this.googleOAuthService = googleOAuthService;
        this.userRepository = userRepository;
        this.jwtService = jwtService;
        this.passwordEncoder = passwordEncoder;
    }

    /**
     * 이메일/비밀번호로 회원가입한다. 이미 가입된 이메일이면 예외를 던진다.
     * findByEmail 사전 체크만으로는 동시 요청 경쟁을 완전히 막지 못한다 — 두 요청이 모두 사전 체크를
     * 통과한 뒤 저장을 시도하면 DB의 email UNIQUE 제약에서 하나가 걸리는데, saveAndFlush로 즉시
     * 반영해 그 경우도 이 메서드 안에서 잡아 동일한 예외로 통일한다.
     * 이 메서드에는 의도적으로 @Transactional을 붙이지 않는다 — 붙이면 saveAndFlush()가 그
     * 트랜잭션에 참여하게 되어, DataIntegrityViolationException을 여기서 잡아도 스프링이 이미
     * 트랜잭션을 rollback-only로 표시해버린다. 그러면 이 메서드가 예외 없이 반환되더라도, 실제
     * 커밋 시점에 rollback-only 상태가 감지되어 UnexpectedRollbackException이 던져진다.
     * @Transactional 없이 두면 saveAndFlush()가 자기 완결적인 트랜잭션으로 실행되어 그 안에서
     * 실패가 바로 확정되므로, 여기서 잡아 변환한 예외가 그대로 호출자에게 전달된다.
     */
    public AuthTokenResponse signup(SignupRequest request) {
        if (userRepository.findByEmail(request.email()).isPresent()) {
            throw new IllegalStateException("이미 가입된 이메일입니다.");
        }
        User user = new User(
            request.email(),
            request.name(),
            PROVIDER_LOCAL,
            request.email(),
            passwordEncoder.encode(request.password())
        );
        try {
            userRepository.saveAndFlush(user);
        } catch (DataIntegrityViolationException e) {
            throw new IllegalStateException("이미 가입된 이메일입니다.");
        }
        return issueTokens(user);
    }

    /** 이메일/비밀번호로 로그인한다. 계정이 없거나 비밀번호가 일치하지 않으면 동일한 예외로 던져 계정 존재 여부를 노출하지 않는다. */
    public AuthTokenResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.email())
            .filter(u -> u.getPasswordHash() != null)
            .filter(u -> passwordEncoder.matches(request.password(), u.getPasswordHash()))
            .orElseThrow(() -> new IllegalArgumentException("이메일 또는 비밀번호가 올바르지 않습니다."));
        return issueTokens(user);
    }

    @Transactional
    public AuthTokenResponse loginWithGoogleCode(String code) {
        GoogleTokenResponse tokenResponse = googleOAuthService.exchangeCode(code);
        GoogleUserInfo userInfo = googleOAuthService.fetchUserInfo(tokenResponse.accessToken());

        User user = userRepository.findByProviderAndProviderId(PROVIDER_GOOGLE, userInfo.sub())
            .orElseGet(() -> userRepository.save(
                new User(userInfo.email(), userInfo.name(), PROVIDER_GOOGLE, userInfo.sub(), null)
            ));

        return issueTokens(user);
    }

    /** [개발용] Google OAuth 없이 데모 계정(provider="demo", providerId=demoUserId)으로 즉시 로그인한다. */
    public AuthTokenResponse devLogin(String demoUserId) {
        User user = userRepository.findByProviderAndProviderId(PROVIDER_DEMO, demoUserId)
            .orElseThrow(() -> new IllegalArgumentException("알 수 없는 테스트 계정입니다: " + demoUserId));
        return issueTokens(user);
    }

    public AuthTokenResponse refresh(String refreshToken) {
        Claims claims = jwtService.parseRefreshToken(refreshToken);
        Long userId = Long.valueOf(claims.getSubject());
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
        return issueTokens(user);
    }

    private AuthTokenResponse issueTokens(User user) {
        String accessToken = jwtService.issueAccessToken(user);
        String refreshToken = jwtService.issueRefreshToken(user);
        UserSummary summary = UserSummary.from(user);
        return new AuthTokenResponse(accessToken, refreshToken, jwtService.accessTokenTtlSeconds(), summary);
    }
}
