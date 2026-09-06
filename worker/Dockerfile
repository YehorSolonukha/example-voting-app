# etap budowania z wymuszeniem architektury hosta (np. x86_64)
FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:7.0 AS builder

# pobranie zmiennej z docelową architekturą (np. arm64)
ARG TARGETARCH

# ustawienie katalogu roboczego
WORKDIR /source

# kopiowanie pliku konfiguracyjnego projektu
COPY *.csproj .
# pobieranie zależności dla docelowej architektury
RUN dotnet restore -a $TARGETARCH

# kopiowanie pozostałych plików kodu źródłowego
COPY . .
# skrośna kompilacja aplikacji dla docelowej architektury
RUN dotnet publish -c release -o /app -a $TARGETARCH --no-restore

# etap uruchomieniowy (zawiera tylko lekkie środowisko wykonawcze)
FROM mcr.microsoft.com/dotnet/runtime:7.0

# ustawienie katalogu roboczego
WORKDIR /app

# kopiowanie skompilowanej aplikacji z etapu budowania
COPY --from=builder /app .

# określenie domyślnego polecenia startowego
ENTRYPOINT ["dotnet", "Worker.dll"]