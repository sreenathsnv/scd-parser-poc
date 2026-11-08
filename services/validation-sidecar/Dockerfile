# upstream image bundles Java 17 but its jar needs 21+; only used as a jar source here
FROM riseclipse/riseclipse-validator-scl:latest AS riseclipse-jar

FROM eclipse-temurin:21-jdk AS build
WORKDIR /build
COPY src ./src
RUN javac -d out src/main/java/com/trivium/validationsidecar/ValidationServer.java

FROM eclipse-temurin:21-jre
WORKDIR /opt/riseclipse

COPY --from=riseclipse-jar /usr/riseclipse/bin/RiseClipseValidatorSCL.jar ./RiseClipseValidatorSCL.jar
COPY --from=build /build/out /opt/validation-sidecar/classes
COPY rules ./rules

ENV RISECLIPSE_JAR=/opt/riseclipse/RiseClipseValidatorSCL.jar \
    RISECLIPSE_OCL_DIR=/opt/riseclipse/rules/ocl \
    RISECLIPSE_NSD_DIR=/opt/riseclipse/rules/nsd \
    WORK_DIR=/tmp/validation-sidecar \
    PORT=8080

EXPOSE 8080
CMD ["java", "-cp", "/opt/validation-sidecar/classes", "com.trivium.validationsidecar.ValidationServer"]
