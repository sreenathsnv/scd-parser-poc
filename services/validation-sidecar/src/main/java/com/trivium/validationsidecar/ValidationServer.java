package com.trivium.validationsidecar;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/** Thin HTTP wrapper around the RiseClipse SCL validator jar. */
public final class ValidationServer {

    private static final Pattern MESSAGE_LINE = Pattern.compile(
            "^(ERROR|WARNING|NOTICE|INFO|DEBUG)\\s*:\\s*\\[(.*?)\\]\\s*(.*?)\\s*\\((.*?):(\\d+)\\)\\s*$");

    private final Path jarPath;
    private final Path oclDir;
    private final Path nsdDir;
    private final Path xsdSchema;
    private final Path workRoot;

    public ValidationServer(Path jarPath, Path oclDir, Path nsdDir, Path xsdSchema, Path workRoot) {
        this.jarPath = jarPath;
        this.oclDir = oclDir;
        this.nsdDir = nsdDir;
        this.xsdSchema = xsdSchema;
        this.workRoot = workRoot;
    }

    public static void main(String[] args) throws IOException {
        Path jarPath = Path.of(System.getenv().getOrDefault("RISECLIPSE_JAR", "/opt/riseclipse/RiseClipseValidatorSCL.jar"));
        Path oclDir = Path.of(System.getenv().getOrDefault("RISECLIPSE_OCL_DIR", "/opt/riseclipse/rules/ocl"));
        Path nsdDir = Path.of(System.getenv().getOrDefault("RISECLIPSE_NSD_DIR", "/opt/riseclipse/rules/nsd"));
        String xsdEnv = System.getenv("SCL_XSD_SCHEMA");
        Path xsdSchema = (xsdEnv == null || xsdEnv.isBlank()) ? null : Path.of(xsdEnv);
        Path workRoot = Path.of(System.getenv().getOrDefault("WORK_DIR", "/tmp/validation-sidecar"));
        Files.createDirectories(workRoot);

        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        ValidationServer server = new ValidationServer(jarPath, oclDir, nsdDir, xsdSchema, workRoot);

        HttpServer http = HttpServer.create(new InetSocketAddress(port), 0);
        http.createContext("/health", server::handleHealth);
        http.createContext("/validate", server::handleValidate);
        http.setExecutor(null);
        http.start();
        System.out.println("validation-sidecar listening on :" + port);
    }

    private void handleHealth(HttpExchange exchange) throws IOException {
        byte[] body = "{\"status\":\"ok\"}".getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, body.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(body);
        }
    }

    private void handleValidate(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            exchange.sendResponseHeaders(405, -1);
            return;
        }
        String filename = queryParam(exchange.getRequestURI(), "filename");
        if (filename == null || filename.isBlank()) {
            filename = "upload.scl";
        }
        Path requestDir = workRoot.resolve(UUID.randomUUID().toString());
        Files.createDirectories(requestDir);
        Path dataDir = requestDir.resolve("data");
        Files.createDirectories(dataDir);
        Path inputFile = dataDir.resolve(sanitizeFilename(filename));

        try (InputStream is = exchange.getRequestBody()) {
            Files.copy(is, inputFile);
        }

        try {
            String json = runValidator(inputFile);
            byte[] body = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        } catch (Exception e) {
            String json = "{\"status\":\"error\",\"message\":" + jsonString(e.toString()) + "}";
            byte[] body = json.getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(500, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        } finally {
            deleteRecursively(requestDir);
        }
    }

    private String runValidator(Path inputFile) throws IOException, InterruptedException {
        boolean oclRulesPresent = Files.isDirectory(oclDir) && hasFiles(oclDir);
        boolean nsdRulesPresent = Files.isDirectory(nsdDir) && hasFiles(nsdDir);
        boolean xsdPresent = xsdSchema != null && Files.isRegularFile(xsdSchema);

        List<String> command = new java.util.ArrayList<>();
        command.add("java");
        command.add("-jar");
        command.add(jarPath.toString());
        command.add("--use-different-exit-codes");
        command.add("--info");
        if (xsdPresent) {
            command.add("--xml-schema");
            command.add(xsdSchema.toString());
        }
        if (oclRulesPresent) {
            command.add(oclDir.toString());
        }
        if (nsdRulesPresent) {
            command.add(nsdDir.toString());
        }
        command.add(inputFile.toString());

        ProcessBuilder pb = new ProcessBuilder(command);
        pb.redirectErrorStream(true);
        Process process = pb.start();
        String output;
        try (InputStream is = process.getInputStream()) {
            output = new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
        int exitCode = process.waitFor();

        List<Finding> findings = parseFindings(output);
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        sb.append("\"status\":\"ok\",");
        sb.append("\"exitCode\":").append(exitCode).append(",");
        sb.append("\"xsdValidationApplied\":").append(xsdPresent).append(",");
        sb.append("\"oclRulesApplied\":").append(oclRulesPresent).append(",");
        sb.append("\"nsdRulesApplied\":").append(nsdRulesPresent).append(",");
        if (!oclRulesPresent) {
            sb.append("\"note\":\"no OCL semantic rules mounted at ").append(oclDir)
              .append(" -- see services/validation-sidecar/README.md to populate them; XSD/structural output only\",");
        }
        sb.append("\"findings\":[");
        sb.append(findings.stream().map(Finding::toJson).collect(Collectors.joining(",")));
        sb.append("]}");
        return sb.toString();
    }

    private List<Finding> parseFindings(String output) {
        return output.lines()
                .map(MESSAGE_LINE::matcher)
                .filter(Matcher::matches)
                .map(mx -> new Finding(mx.group(1), mx.group(2), mx.group(3), mx.group(4), mx.group(5)))
                .collect(Collectors.toList());
    }

    private record Finding(String severity, String category, String message, String file, String line) {
        String toJson() {
            return "{" +
                    "\"severity\":" + jsonString(severity.toLowerCase(java.util.Locale.ROOT)) + "," +
                    "\"category\":" + jsonString(category) + "," +
                    "\"message\":" + jsonString(message) + "," +
                    "\"file\":" + jsonString(file) + "," +
                    "\"line\":" + line +
                    "}";
        }
    }

    private static String jsonString(String s) {
        StringBuilder sb = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
                }
            }
        }
        return sb.append('"').toString();
    }

    private static boolean hasFiles(Path dir) throws IOException {
        try (var stream = Files.list(dir)) {
            return stream.anyMatch(p -> !p.getFileName().toString().startsWith("."));
        }
    }

    private static String queryParam(URI uri, String name) {
        String query = uri.getRawQuery();
        if (query == null) return null;
        for (String pair : query.split("&")) {
            int idx = pair.indexOf('=');
            if (idx < 0) continue;
            String key = java.net.URLDecoder.decode(pair.substring(0, idx), StandardCharsets.UTF_8);
            if (key.equals(name)) {
                return java.net.URLDecoder.decode(pair.substring(idx + 1), StandardCharsets.UTF_8);
            }
        }
        return null;
    }

    private static String sanitizeFilename(String filename) {
        String base = Path.of(filename).getFileName().toString();
        return base.replaceAll("[^A-Za-z0-9._-]", "_");
    }

    private static void deleteRecursively(Path path) {
        try {
            if (!Files.exists(path)) return;
            Files.walk(path)
                    .sorted(java.util.Comparator.reverseOrder())
                    .forEach(p -> {
                        try {
                            Files.delete(p);
                        } catch (IOException ignored) {
                        }
                    });
        } catch (IOException ignored) {
        }
    }
}
