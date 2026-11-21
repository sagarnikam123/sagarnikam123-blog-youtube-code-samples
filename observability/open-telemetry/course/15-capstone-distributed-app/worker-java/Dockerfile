FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /build/target/capstone-worker-1.0.0.jar app.jar
EXPOSE 8090
CMD ["java", "-jar", "app.jar"]
