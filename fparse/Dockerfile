FROM gradle:6.5.0-jdk11 AS build
COPY --chown=gradle:gradle . /home/gradle/src
WORKDIR /home/gradle/src
RUN gradle build --no-daemon --stacktrace -x test

FROM openjdk:11.0.7-jdk-slim
RUN mkdir -p /app
COPY --from=build /home/gradle/src/build/libs/*.jar /app/app.jar
WORKDIR /app
ENTRYPOINT ["java", "-Dserver.port=4219", "-jar", "/app/app.jar"]
EXPOSE 4219
