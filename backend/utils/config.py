import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env (se existir)
# Crie um arquivo .env na raiz do backend/ com suas variáveis
# Exemplo .env:
# DB_HOST=localhost
# DB_NAME=reconhecimento_facial
# DB_USER=meu_usuario
# DB_PASS=Innovate@V8
load_dotenv()

class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "reconhecimento_facial")
    DB_USER: str = os.getenv("DB_USER", "meu_usuario")
    DB_PASS: str = os.getenv("DB_PASS", "Innovate@V8") # Mantenha senhas fora do código em produção
    # Adicione outras configurações aqui conforme necessário

settings = Settings()