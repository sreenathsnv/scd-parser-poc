FROM eclipse-temurin:21-jdk AS build
WORKDIR /build
COPY src ./src
RUN javac -d out src/main/java/com/trivium/modelgenerator/ModelGeneratorServer.java

FROM eclipse-temurin:21-jre
COPY --from=build /build/out /opt/model-generator/classes
ENV PORT=8080
EXPOSE 8080
CMD ["java", "-cp", "/opt/model-generator/classes", "com.trivium.modelgenerator.ModelGeneratorServer"]
