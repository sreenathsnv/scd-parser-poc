package com.trivium.modelgenerator;

import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

/** Placeholder for Phase 3's genconfig.jar-based model/config generator. */
public final class ModelGeneratorServer {

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        HttpServer http = HttpServer.create(new InetSocketAddress(port), 0);
        http.createContext("/health", exchange -> {
            byte[] body = "{\"status\":\"ok\"}".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });
        http.createContext("/generate", exchange -> {
            String message = "{\"status\":\"not_implemented\",\"message\":"
                    + "\"model-generator is scaffolded for Phase 0; genconfig.jar wiring lands in Phase 3\"}";
            byte[] body = message.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(501, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });
        http.setExecutor(null);
        http.start();
        System.out.println("model-generator listening on :" + port);
    }
}
