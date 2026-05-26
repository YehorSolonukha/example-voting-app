FROM mcr.microsoft.com/dotnet/sdk:7.0 AS builder

WORKDIR /source

# deps
COPY *.csproj .
RUN dotnet restore

# compile
COPY . .
RUN dotnet publish -c release -o /app --no-restore


FROM mcr.microsoft.com/dotnet/runtime:7.0

WORKDIR /app

# copy only compiled
COPY --from=builder /app .

ENTRYPOINT ["dotnet", "Worker.dll"]