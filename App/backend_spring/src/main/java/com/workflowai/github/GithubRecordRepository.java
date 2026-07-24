package com.workflowai.github;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface GithubRecordRepository extends JpaRepository<GithubRecord, Long> {
    @Query("select distinct g.projectId from GithubRecord g where g.projectId in :projectIds")
    List<Long> findDistinctProjectIdsIn(@Param("projectIds") List<Long> projectIds);
}
