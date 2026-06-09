# ETAP 1 - Kompilacja w środowisku SDK
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS builder

WORKDIR /source

# Kopiowanie manifestu projektu i pobieranie zależności.
COPY *.csproj .
RUN dotnet restore

# Kopiowanie pozostałego kodu źródłowego aplikacji.
COPY . .
RUN dotnet publish -c release -o /app --no-restore


# ETAP 2 - Środowisko produkcyjne
FROM mcr.microsoft.com/dotnet/runtime:7.0
WORKDIR /app

# Kopiowanie wyłącznie gotowych plików binarnych z pierwszego etapu.
COPY --from=builder /app .

ENTRYPOINT ["dotnet", "Worker.dll"]


