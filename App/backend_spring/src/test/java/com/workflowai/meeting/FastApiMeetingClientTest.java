package com.workflowai.meeting;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClientException;

class FastApiMeetingClientTest {

    @Test
    void transcribeAudioReturnsTextFromFastApiResponse() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/api/v1/meetings/transcribe", exchange -> {
            byte[] body = "{\"text\":\"음성에서 추출된 텍스트\"}".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            try (var os = exchange.getResponseBody()) {
                os.write(body);
            }
        });
        server.start();

        try {
            FastApiMeetingClient client = new FastApiMeetingClient(
                "http://127.0.0.1:" + server.getAddress().getPort(),
                Duration.ofSeconds(2),
                Duration.ofSeconds(2)
            );

            String text = client.transcribeAudio("fake-audio-bytes".getBytes(StandardCharsets.UTF_8), "meeting.wav");

            assertThat(text).isEqualTo("음성에서 추출된 텍스트");
        } finally {
            server.stop(0);
        }
    }

    @Test
    void analyzeStopsWhenReadTimeoutExpires() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/api/v1/meetings/analyze-json", exchange -> {
            try {
                Thread.sleep(1_000);
                exchange.sendResponseHeaders(200, 0);
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
            } finally {
                exchange.close();
            }
        });
        server.start();

        try {
            FastApiMeetingClient client = new FastApiMeetingClient(
                "http://127.0.0.1:" + server.getAddress().getPort(),
                Duration.ofMillis(100),
                Duration.ofMillis(100)
            );
            long startedAt = System.nanoTime();

            assertThatThrownBy(() -> client.analyze(request()))
                .isInstanceOf(RestClientException.class);

            assertThat(Duration.ofNanos(System.nanoTime() - startedAt))
                .isLessThan(Duration.ofSeconds(2));
        } finally {
            server.stop(0);
        }
    }

    private static AiAnalyzeRequest request() {
        return new AiAnalyzeRequest(
            "project-1",
            "주간 회의",
            "2026-07-23",
            "weekly",
            "text",
            null,
            "회의 본문",
            List.of("김민준")
        );
    }
}
