package com.workflowai.auth;

import com.workflowai.common.ApiResponse;
import com.workflowai.project.Project;
import com.workflowai.project.ProjectMember;
import com.workflowai.project.ProjectMemberRepository;
import com.workflowai.project.ProjectRepository;
import com.workflowai.security.CurrentUser;
import com.workflowai.user.User;
import com.workflowai.user.UserRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@Tag(name = "내 정보", description = "현재 로그인한 사용자의 기본 정보 및 역할 요약")
@RestController
@RequestMapping("/api/v1/me")
public class MeController {
    private static final Set<String> ALLOWED_AVATAR_TYPES = Set.of("image/png", "image/jpeg");
    private static final long MAX_AVATAR_BYTES = 10L * 1024 * 1024;

    private final UserRepository userRepository;
    private final ProjectMemberRepository projectMemberRepository;
    private final ProjectRepository projectRepository;
    private final String uploadsDir;

    public MeController(
        UserRepository userRepository,
        ProjectMemberRepository projectMemberRepository,
        ProjectRepository projectRepository,
        @Value("${workflow.uploads.dir}") String uploadsDir
    ) {
        this.userRepository = userRepository;
        this.projectMemberRepository = projectMemberRepository;
        this.projectRepository = projectRepository;
        this.uploadsDir = uploadsDir;
    }

    @Operation(summary = "내 정보 조회", description = "현재 로그인한 사용자의 기본 정보와 프로젝트별 역할을 조회한다.")
    @GetMapping
    public ApiResponse<MeResponse> me() {
        User user = userRepository.findById(CurrentUser.id())
            .orElseThrow(() -> new IllegalStateException("사용자를 찾을 수 없습니다."));

        List<ProjectMember> memberships = projectMemberRepository.findAllByUserId(user.getId());
        Map<Long, Project> projectsById = projectRepository
            .findAllById(memberships.stream().map(ProjectMember::getProjectId).toList())
            .stream()
            .collect(Collectors.toMap(Project::getId, project -> project));

        List<ProjectRoleSummary> projectRoles = memberships.stream()
            .map(pm -> {
                Project project = projectsById.get(pm.getProjectId());
                String title = project != null ? project.getTitle() : null;
                return new ProjectRoleSummary(pm.getProjectId(), title, pm.getRole().toKorean());
            })
            .toList();

        return ApiResponse.ok(new MeResponse(UserSummary.from(user), projectRoles));
    }

    @Operation(
        summary = "내 정보 수정",
        description = "이름/소속/분야/GitHub 아이디를 수정한다. 요청에 없는(null) 필드는 기존 값을 유지한다."
    )
    @PatchMapping
    @Transactional
    public ApiResponse<UserSummary> updateMe(@RequestBody UpdateMeRequest request) {
        User user = userRepository.findById(CurrentUser.id())
            .orElseThrow(() -> new IllegalStateException("사용자를 찾을 수 없습니다."));

        if (request.name() != null) {
            user.setName(request.name());
        }
        if (request.affiliation() != null) {
            user.setAffiliation(request.affiliation());
        }
        if (request.field() != null) {
            user.setField(request.field());
        }
        if (request.githubUsername() != null) {
            user.setGithubUsername(request.githubUsername());
        }

        return ApiResponse.ok(UserSummary.from(user));
    }

    @Operation(
        summary = "프로필 사진 업로드",
        description = "PNG/JPG만 허용하며 최대 10MB까지 업로드할 수 있다. 기존 사진이 있으면 교체된다."
    )
    @PostMapping(value = "/avatar", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Transactional
    public ResponseEntity<ApiResponse<UserSummary>> uploadAvatar(
        @Parameter(description = "프로필 사진 파일 (PNG/JPG, 최대 10MB)") @RequestPart("file") MultipartFile file
    ) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.fail("EMPTY_FILE", "파일을 선택해주세요."));
        }
        if (!ALLOWED_AVATAR_TYPES.contains(file.getContentType())) {
            return ResponseEntity.badRequest()
                .body(ApiResponse.fail("INVALID_FILE_TYPE", "PNG 또는 JPG 파일만 업로드할 수 있습니다."));
        }
        if (file.getSize() > MAX_AVATAR_BYTES) {
            return ResponseEntity.badRequest()
                .body(ApiResponse.fail("FILE_TOO_LARGE", "파일 용량은 최대 10MB까지 업로드할 수 있습니다."));
        }

        User user = userRepository.findById(CurrentUser.id())
            .orElseThrow(() -> new IllegalStateException("사용자를 찾을 수 없습니다."));

        try {
            user.setProfileImagePath(storeAvatar(user.getId(), file));
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.fail("UPLOAD_FAILED", "이미지 업로드에 실패했습니다."));
        }

        return ResponseEntity.ok(ApiResponse.ok(UserSummary.from(user)));
    }

    @Operation(
        summary = "내가 담당한 업무 목록",
        description = "업무 데이터 연동은 회의록/업무 보드 담당 기능에서 채워진다. 현재는 빈 목록을 반환하는 스텁이다."
    )
    @GetMapping("/tasks")
    public ApiResponse<List<Object>> myTasks() {
        return ApiResponse.ok(List.of());
    }

    @Operation(
        summary = "내가 받은/작성한 개인 코멘트",
        description = "코멘트 데이터 연동은 별도 기능 담당에서 채워진다. 현재는 빈 목록을 반환하는 스텁이다."
    )
    @GetMapping("/comments")
    public ApiResponse<List<Object>> myComments() {
        return ApiResponse.ok(List.of());
    }

    /** 사용자당 파일 하나만 유지한다: avatars/{userId}.{ext}에 저장하고, 확장자가 바뀌었을 수 있으니 이전 파일은 지운다. */
    private String storeAvatar(Long userId, MultipartFile file) throws IOException {
        Path dir = Path.of(uploadsDir, "avatars").toAbsolutePath().normalize();
        Files.createDirectories(dir);

        for (String ext : List.of("png", "jpg", "jpeg")) {
            Files.deleteIfExists(dir.resolve(userId + "." + ext));
        }

        String extension = file.getContentType().equals("image/png") ? "png" : "jpg";
        String fileName = userId + "." + extension;
        file.transferTo(dir.resolve(fileName));
        return "avatars/" + fileName;
    }
}
