package com.workflowai.auth;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "내 정보 수정 요청 (전달된 필드만 갱신)")
public record UpdateMeRequest(String name, String affiliation, List<String> field, String githubUsername) {
}
