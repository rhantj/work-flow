package com.workflowai.evaluation;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

@ExtendWith(MockitoExtension.class)
class EvaluationScoreControllerTest {

    @Mock
    private EvaluationScoreRepository evaluationScoreRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    private MockMvc mockMvc() {
        return MockMvcBuilders.standaloneSetup(new EvaluationScoreController(evaluationScoreRepository)).build();
    }

    @Test
    void upsertSavesReviewerScoreAndGradeFromCalculator() throws Exception {
        when(evaluationScoreRepository.findByProjectIdAndUserId(1L, 3L)).thenReturn(Optional.empty());
        when(evaluationScoreRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));

        EvaluationScoreRequest request = new EvaluationScoreRequest(
            1L, 3L, new BigDecimal("77.20"), false, new BigDecimal("90.00"), "A+"
        );

        mockMvc().perform(post("/api/v1/projects/1/evaluations")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data.score").value(77.20))
            .andExpect(jsonPath("$.data.reviewerScore").value(90.00))
            .andExpect(jsonPath("$.data.grade").value("A+"));
    }

    @Test
    void upsertKeepsExistingReviewerScoreAndGradeWhenTogglingPublicOnly() throws Exception {
        // 메인 테이블의 공개/비공개 토글은 reviewerScore/grade 없이 호출된다 —
        // 이미 학점 계산기에서 저장해 둔 값을 덮어쓰면 안 된다.
        EvaluationScore existing = new EvaluationScore(1L, 3L, new BigDecimal("77.20"), false);
        existing.setReviewerScore(new BigDecimal("90.00"));
        existing.setGrade("A+");
        when(evaluationScoreRepository.findByProjectIdAndUserId(1L, 3L)).thenReturn(Optional.of(existing));
        when(evaluationScoreRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));

        EvaluationScoreRequest request = new EvaluationScoreRequest(
            1L, 3L, new BigDecimal("77.20"), true, null, null
        );

        mockMvc().perform(post("/api/v1/projects/1/evaluations")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data.isPublic").value(true))
            .andExpect(jsonPath("$.data.reviewerScore").value(90.00))
            .andExpect(jsonPath("$.data.grade").value("A+"));
    }

    @Test
    void listReturnsReviewerScoreAndGradeFields() throws Exception {
        EvaluationScore saved = new EvaluationScore(1L, 3L, new BigDecimal("77.20"), true);
        saved.setReviewerScore(new BigDecimal("90.00"));
        saved.setGrade("A+");
        when(evaluationScoreRepository.findAllByProjectId(1L)).thenReturn(List.of(saved));

        mockMvc().perform(get("/api/v1/projects/1/evaluations"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data[0].reviewerScore").value(90.00))
            .andExpect(jsonPath("$.data[0].grade").value("A+"));
    }
}
