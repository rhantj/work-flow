package com.workflowai.deliverable;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface DeliverableRepository extends JpaRepository<Deliverable, Long> {
    @Query("""
        select d.projectId as projectId,
               count(d.id) as totalCount,
               sum(case when d.status = :finalStatus then 1 else 0 end) as submittedCount
        from Deliverable d
        where d.projectId in :projectIds
        group by d.projectId
        """)
    List<DeliverableProgressView> summarizeByProjectIds(
        @Param("projectIds") List<Long> projectIds,
        @Param("finalStatus") String finalStatus
    );

    interface DeliverableProgressView {
        Long getProjectId();

        Long getTotalCount();

        Long getSubmittedCount();
    }
}
