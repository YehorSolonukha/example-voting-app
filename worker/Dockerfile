FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:7.0 AS builder

ARG TARGETARCH

WORKDIR /source

COPY *.csproj .
RUN dotnet restore -a $TARGETARCH

COPY . .
RUN dotnet publish -c release -o /app -a $TARGETARCH --no-restore

FROM mcr.microsoft.com/dotnet/runtime:7.0
WORKDIR /app

COPY --from=builder /app .

ENTRYPOINT ["dotnet", "Worker.dll"]


