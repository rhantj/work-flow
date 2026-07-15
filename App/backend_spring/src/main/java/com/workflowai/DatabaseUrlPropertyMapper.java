package com.workflowai;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

final class DatabaseUrlPropertyMapper {
    private static final String SPRING_DATASOURCE_URL = "spring.datasource.url";
    private static final String SPRING_DATASOURCE_USERNAME = "spring.datasource.username";
    private static final String SPRING_DATASOURCE_PASSWORD = "spring.datasource.password";

    private DatabaseUrlPropertyMapper() {
    }

    static void apply() {
        Map<String, String> properties = toSpringProperties(System.getenv());
        properties.forEach((key, value) -> {
            if (!hasText(System.getProperty(key))) {
                System.setProperty(key, value);
            }
        });
    }

    static Map<String, String> toSpringProperties(Map<String, String> env) {
        Map<String, String> properties = new LinkedHashMap<>();
        if (hasText(env.get("SPRING_DATASOURCE_URL"))) {
            return properties;
        }

        String databaseUrl = env.get("DATABASE_URL");
        if (hasText(databaseUrl)) {
            properties.putAll(fromDatabaseUrl(databaseUrl, env));
        }

        if (properties.isEmpty()) {
            properties.putAll(fromPgVariables(env));
        }
        return properties;
    }

    private static Map<String, String> fromDatabaseUrl(String databaseUrl, Map<String, String> env) {
        Map<String, String> properties = new LinkedHashMap<>();
        if (databaseUrl.startsWith("jdbc:postgresql://")) {
            properties.put(SPRING_DATASOURCE_URL, databaseUrl);
            return properties;
        }

        URI uri;
        try {
            uri = URI.create(databaseUrl);
        } catch (IllegalArgumentException ignored) {
            return properties;
        }

        String scheme = uri.getScheme();
        if (!"postgres".equals(scheme) && !"postgresql".equals(scheme)) {
            return properties;
        }

        String host = uri.getHost();
        if (!hasText(host)) {
            return properties;
        }

        int port = uri.getPort() < 0 ? 5432 : uri.getPort();
        String path = hasText(uri.getRawPath()) ? uri.getRawPath() : "/postgres";
        String query = hasText(uri.getRawQuery()) ? "?" + uri.getRawQuery() : "";
        properties.put(SPRING_DATASOURCE_URL, "jdbc:postgresql://" + host + ":" + port + path + query);

        String rawUserInfo = uri.getRawUserInfo();
        if (hasText(rawUserInfo)) {
            int separator = rawUserInfo.indexOf(':');
            String username = separator < 0 ? rawUserInfo : rawUserInfo.substring(0, separator);
            String password = separator < 0 ? "" : rawUserInfo.substring(separator + 1);
            putIfSpringEnvMissing(properties, env, "SPRING_DATASOURCE_USERNAME", SPRING_DATASOURCE_USERNAME, decode(username));
            putIfSpringEnvMissing(properties, env, "SPRING_DATASOURCE_PASSWORD", SPRING_DATASOURCE_PASSWORD, decode(password));
        }

        return properties;
    }

    private static Map<String, String> fromPgVariables(Map<String, String> env) {
        Map<String, String> properties = new LinkedHashMap<>();
        String host = env.get("PGHOST");
        String database = env.get("PGDATABASE");
        if (!hasText(host) || !hasText(database)) {
            return properties;
        }

        String port = hasText(env.get("PGPORT")) ? env.get("PGPORT") : "5432";
        String sslMode = hasText(env.get("PGSSLMODE")) ? "?sslmode=" + env.get("PGSSLMODE") : "";
        properties.put(SPRING_DATASOURCE_URL, "jdbc:postgresql://" + host + ":" + port + "/" + database + sslMode);
        putIfSpringEnvMissing(properties, env, "SPRING_DATASOURCE_USERNAME", SPRING_DATASOURCE_USERNAME, env.get("PGUSER"));
        putIfSpringEnvMissing(properties, env, "SPRING_DATASOURCE_PASSWORD", SPRING_DATASOURCE_PASSWORD, env.get("PGPASSWORD"));
        return properties;
    }

    private static void putIfSpringEnvMissing(
        Map<String, String> properties,
        Map<String, String> env,
        String envKey,
        String propertyKey,
        String value
    ) {
        if (!hasText(env.get(envKey)) && hasText(value)) {
            properties.put(propertyKey, value);
        }
    }

    private static String decode(String value) {
        return URLDecoder.decode(value, StandardCharsets.UTF_8);
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
