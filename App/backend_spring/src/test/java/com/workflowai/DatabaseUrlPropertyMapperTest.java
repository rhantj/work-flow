package com.workflowai;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.util.Map;
import org.junit.jupiter.api.Test;

class DatabaseUrlPropertyMapperTest {

    @Test
    void convertsDatabaseUrlToSpringDatasourceProperties() {
        Map<String, String> properties = DatabaseUrlPropertyMapper.toSpringProperties(Map.of(
            "DATABASE_URL",
            "postgresql://postgres.zzfcnbbzmbxzxptxghhq:p%40ssword@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"
        ));

        assertEquals(
            "jdbc:postgresql://aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require",
            properties.get("spring.datasource.url")
        );
        assertEquals("postgres.zzfcnbbzmbxzxptxghhq", properties.get("spring.datasource.username"));
        assertEquals("p@ssword", properties.get("spring.datasource.password"));
    }

    @Test
    void convertsPgVariablesToSpringDatasourceProperties() {
        Map<String, String> properties = DatabaseUrlPropertyMapper.toSpringProperties(Map.of(
            "PGHOST", "postgres.internal",
            "PGPORT", "5432",
            "PGDATABASE", "workflow",
            "PGUSER", "postgres",
            "PGPASSWORD", "root"
        ));

        assertEquals("jdbc:postgresql://postgres.internal:5432/workflow", properties.get("spring.datasource.url"));
        assertEquals("postgres", properties.get("spring.datasource.username"));
        assertEquals("root", properties.get("spring.datasource.password"));
    }

    @Test
    void keepsExplicitSpringDatasourceUrlUntouched() {
        Map<String, String> properties = DatabaseUrlPropertyMapper.toSpringProperties(Map.of(
            "SPRING_DATASOURCE_URL", "jdbc:postgresql://db:5432/workflow",
            "DATABASE_URL", "postgresql://ignored:ignored@localhost:5432/ignored"
        ));

        assertFalse(properties.containsKey("spring.datasource.url"));
    }
}
