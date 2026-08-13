FROM python:3.11-slim

# Evita arquivos .pyc no disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita buffer de logs no terminal
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala ferramentas básicas de compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos do backend e do frontend para o contêiner
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Altera o diretório de execução para o backend
WORKDIR /app/backend

# Expõe a porta 8001 para o mundo externo
EXPOSE 8001

# Comando para rodar a aplicação
CMD ["python", "app.py"]
