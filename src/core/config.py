import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Configuração Centralizada da Aplicação.
    Valida variáveis de ambiente no startup.
    """
    # Google Cloud / Vertex AI
    PROJECT_ID: str = "amazing-firefly-475113-p3"
    LOCATION: str = "us-central1"
    MODEL_ID: str = "gemini-1.5-pro-preview-0409" # Atualizado para versão estável mais recente se possível

    # Segurança
    API_KEY: str
    
    # Aplicação
    APP_TITLE: str = "MariIA - Sales Intelligence"
    APP_VERSION: str = "1.0.0"
    
    # Database (Placeholder para futuro)
    # DB_CONNECTION_STRING: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignora variáveis extras no .env

@lru_cache()
def get_settings():
    """Retorna instância singleton das configurações."""
    # Em produção, isso falhará se API_KEY não estiver no env, o que é desejado (Fail fast)
    return Settings()
