package com.course;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class PlainServer {

    public static void main(String[] args) throws IOException {
        int port = 8086;
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.createContext("/orders", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                String response = "[{\"id\": 101, \"item\": \"tablet\"}]";
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(response.getBytes());
                }
            }
        });

        System.out.println("Plain Java Server started on port " + port + " (Zero OTel code!)...");
        server.start();
    }
}
