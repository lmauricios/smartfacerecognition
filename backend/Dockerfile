FROM python:3.10-slim-bullseye

# Instala dependências do sistema operacional necessárias para opencv, dlib, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgtk2.0-dev \
    pkg-config \
    libatlas-base-dev \
    gfortran \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    # Dependências para dlib/face_recognition (algumas podem já estar acima)
    libboost-python-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Cria um usuário e grupo não-root para rodar a aplicação
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Define o diretório de trabalho dentro do contêiner.
WORKDIR /app

ENV PYTHONUNBUFFERED=True
ENV PORT=8080
# Para FastAPI/Uvicorn, o host 0.0.0.0 é importante dentro do contêiner
ENV HOST=0.0.0.0

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY --chown=appuser:appgroup . .

USER appuser


# Comando para executar a aplicação FastAPI com Uvicorn
CMD ["uvicorn", "main:app", "--host", "$HOST", "--port", "$PORT"]