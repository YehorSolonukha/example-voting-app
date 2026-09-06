FROM python:3.11-slim

WORKDIR /app

# kopiowanie pliku, który zawiera listę zależności
COPY requirements.txt . 
# pobieranie zależności
RUN pip install --no-cache-dir -r requirements.txt 
# kopiowanie pozostałych plików
COPY . . 

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090"]
