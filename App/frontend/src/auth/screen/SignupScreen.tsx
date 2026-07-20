import { useState, type ChangeEvent } from "react";
import { useNavigate } from "react-router";
import { Mail, Lock, Eye, EyeOff, ArrowRight } from "lucide-react";
import { AuthBrandPanel } from "../components/AuthBrandPanel";
import { AuthInput } from "../components/AuthInput";
import { useAuth } from "../../global/hooks/useAuth";
import { API_BASE_URL, type ApiEnvelope } from "../../global/api/apiClient";
import type { AuthTokenResponse } from "../../global/api/authTypes";
import { tokenStore } from "../../global/api/tokenStore";

const DEV_TEST_ACCOUNTS = [
  { id: "1", name: "김민준", role: "팀장" },
  { id: "2", name: "이서연", role: "팀원" },
  { id: "3", name: "박지수", role: "팀원" },
  { id: "4", name: "최동혁", role: "심사자" },
];
const demoAuthEnabled = import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEMO_AUTH === "true";

export function SignupScreen() {
  const navigate = useNavigate();
  const { loginWithGoogle, refreshMe } = useAuth();
  const [judgeSignup, setJudgeSignup] = useState(false);
  const [affiliation, setAffiliation] = useState("");
  const [professorCode, setProfessorCode] = useState("");
  const [certificateFileName, setCertificateFileName] = useState("");
  const [signupError, setSignupError] = useState<string | null>(null);
  const [demoId, setDemoId] = useState("");
  const [demoPw, setDemoPw] = useState("");
  const [showDemoPw, setShowDemoPw] = useState(false);
  const [demoSignupError, setDemoSignupError] = useState<string | null>(null);
  const [demoSigningUp, setDemoSigningUp] = useState(false);

  const handleCertificateChange = (event: ChangeEvent<HTMLInputElement>) => {
    setCertificateFileName(event.target.files?.[0]?.name ?? "");
  };

  const handleSignup = () => {
    setSignupError(null);

    if (judgeSignup && (!affiliation.trim() || !professorCode.trim())) {
      setSignupError("소속 학교/기관과 교수 인증번호를 입력해주세요.");
      return;
    }

    // 심사자 인증 심사(소속/교수 인증번호/서류) 백엔드가 아직 없어, 우선 일반 Google 가입/로그인으로 연결한다.
    loginWithGoogle();
  };

  // 데모 ID/PW 회원가입: 실제 계정 생성 백엔드는 없음 — 데모 계정 이름/번호로 매칭해
  // 기존 dev-login-token 발급 흐름을 그대로 재사용한다(LoginScreen의 데모 로그인과 동일한 방식).
  const handleDemoSignup = async () => {
    if (demoSigningUp) return;
    setDemoSignupError(null);
    const matched = DEV_TEST_ACCOUNTS.find(account => account.id === demoId.trim() || account.name === demoId.trim());
    if (!matched) {
      setDemoSignupError("데모 환경에서는 새 계정을 만들 수 없습니다. 이름(예: 김민준) 또는 번호(1~4)의 기존 데모 계정으로 입장해주세요.");
      return;
    }
    setDemoSigningUp(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/dev-login-token/${matched.id}`);
      const body = await response.json() as ApiEnvelope<AuthTokenResponse>;
      if (!response.ok || !body.success || !body.data?.accessToken || !body.data?.refreshToken) {
        throw new Error(body.error?.message ?? "데모 회원가입에 실패했습니다.");
      }
      tokenStore.clear();
      tokenStore.setTokens(body.data.accessToken, body.data.refreshToken);
      await refreshMe();
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setDemoSignupError(error instanceof Error ? error.message : "데모 회원가입에 실패했습니다.");
    } finally {
      setDemoSigningUp(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col lg:flex-row" style={{ fontFamily: "'Inter', 'Noto Sans KR', sans-serif" }}>
      <AuthBrandPanel />

      <div className="flex-1 flex items-center justify-center bg-background px-8">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-foreground mb-1">TeamFlow AI 시작하기</h1>
            <p className="text-sm text-muted-foreground">
              Google 계정 하나로 가입과 로그인이 한번에 끝나요. 팀 프로젝트를 스마트하게 관리해보세요.
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={handleSignup}
              className="w-full py-3 rounded-xl border border-border bg-card text-sm font-semibold text-foreground transition-all hover:bg-muted flex items-center justify-center gap-2.5"
            >
              <GoogleIcon />
              {judgeSignup ? "심사자 가입 신청하기" : "Google로 시작하기"}
            </button>

            <label className={`block rounded-2xl border p-4 transition-all cursor-pointer ${judgeSignup ? "border-blue-400 bg-blue-50" : "border-border bg-card hover:bg-muted/50"}`}>
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={judgeSignup}
                  onChange={event => {
                    setJudgeSignup(event.target.checked);
                    setSignupError(null);
                  }}
                  className="mt-1 h-4 w-4 rounded border-border accent-blue-600"
                />
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-foreground">교수/심사자로 가입 신청</div>
                  <div className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    입력한 인증 정보는 Google 가입 후 관리자가 별도로 확인합니다. (자동 승인 아님)
                  </div>
                </div>
              </div>
            </label>

            {judgeSignup && (
              <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-4 space-y-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">소속 학교/기관</label>
                  <input
                    value={affiliation}
                    onChange={event => setAffiliation(event.target.value)}
                    placeholder="예: 한국대학교 컴퓨터공학과"
                    className="w-full rounded-xl border border-blue-100 bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">교수 인증번호</label>
                  <input
                    value={professorCode}
                    onChange={event => setProfessorCode(event.target.value)}
                    placeholder="교수 일련번호 또는 인증 코드"
                    className="w-full rounded-xl border border-blue-100 bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">인증서류 첨부</label>
                  <label className="flex min-h-11 cursor-pointer items-center justify-between gap-3 rounded-xl border border-dashed border-blue-200 bg-white px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-blue-400">
                    <span className="truncate">{certificateFileName || "재직증명서 또는 심사자 인증 서류"}</span>
                    <span className="shrink-0 text-xs font-semibold text-blue-600">파일 선택</span>
                    <input type="file" className="hidden" onChange={handleCertificateChange} />
                  </label>
                </div>
                <div className="rounded-xl bg-blue-100/60 border border-blue-200 px-3 py-2.5 text-xs text-blue-800 leading-relaxed">
                  가입 신청 후 <strong>관리자 승인 절차</strong>를 거칩니다. 승인이 완료되면 심사자 권한으로 로그인됩니다.
                </div>
              </div>
            )}

            {signupError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">
                {signupError}
              </div>
            )}
          </div>

          <p className="text-center text-[11px] text-muted-foreground mt-4 leading-relaxed">
            계속 진행하면 이용약관 및 개인정보처리방침에 동의하는 것으로 간주됩니다.
          </p>

          <p className="text-center text-sm text-muted-foreground mt-6">
            이미 계정이 있으신가요?{" "}
            <button onClick={() => navigate("/login")} className="font-semibold text-blue-600 hover:text-blue-700 transition-colors">
              로그인
            </button>
          </p>

          {demoAuthEnabled && (
            <div className="mt-8 pt-6 border-t border-border">
              <p className="text-center text-[11px] font-semibold text-amber-600 mb-3">
                ⚠ 개발/데모 전용 — 실제 계정을 생성하지 않습니다
              </p>
              <div className="space-y-3">
                <AuthInput
                  label="데모 ID (계정 이름 또는 번호)" type="text" placeholder="예: 김민준 또는 1"
                  value={demoId} onChange={setDemoId} icon={Mail}
                />
                <AuthInput
                  label="비밀번호 (데모 - 검증하지 않음)" type={showDemoPw ? "text" : "password"} placeholder="아무 값이나 입력"
                  value={demoPw} onChange={setDemoPw} icon={Lock}
                  right={
                    <button type="button" onClick={() => setShowDemoPw(v => !v)} className="text-muted-foreground hover:text-foreground transition-colors">
                      {showDemoPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  }
                />
                {demoSignupError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[11px] text-red-600">
                    {demoSignupError}
                  </div>
                )}
                <button
                  onClick={() => void handleDemoSignup()}
                  disabled={demoSigningUp}
                  className="w-full py-2.5 rounded-xl text-white text-sm font-semibold transition-all disabled:opacity-70 hover:opacity-90 flex items-center justify-center gap-2"
                  style={{ background: "linear-gradient(135deg, #3B5BDB 0%, #4F6EF7 100%)" }}
                >
                  <ArrowRight className="w-4 h-4" /> {demoSigningUp ? "처리 중..." : "ID/PW로 회원가입 (데모)"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 15.9 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6 29.6 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.5 0 10.4-1.9 14.3-5.1l-6.6-5.6C29.7 34.9 27 36 24 36c-5.2 0-9.6-3.3-11.2-7.9l-6.6 5.1C9.6 39.6 16.3 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4.1 5.6l6.6 5.6C39.5 37.4 44 31.3 44 24c0-1.3-.1-2.7-.4-3.5z" />
    </svg>
  );
}
