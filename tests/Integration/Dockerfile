# syntax=docker/dockerfile:1
# Integration test container that runs the CLI against real or sample providers
# and compares output against a baseline (legacy Python script).

ARG DOTNET_VERSION=10.0

FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION} AS build

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 curl ca-certificates diffutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy solution and project files for restore
COPY M3Undle.Cli.slnx ./
COPY global.json ./
COPY nuget.config ./
COPY src/CliVersion.props src/Directory.Build.props src/
COPY src/M3Undle.Cli/M3Undle.Cli.csproj src/M3Undle.Cli/
COPY tests/M3Undle.Cli.Tests/M3Undle.Cli.Tests.csproj tests/M3Undle.Cli.Tests/

RUN dotnet restore M3Undle.Cli.slnx

# Copy all source
COPY src/ src/

# Build the CLI project
RUN dotnet build src/M3Undle.Cli/M3Undle.Cli.csproj -c Release --no-restore

# Copy integration test assets
COPY tests/Integration/ /opt/integration/

WORKDIR /opt/integration

ENTRYPOINT ["bash", "/opt/integration/entrypoint.sh"]
