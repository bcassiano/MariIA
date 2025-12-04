import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import urllib.parse

# Carrega variáveis de ambiente
load_dotenv()

class DatabaseConnector:
    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_DATABASE")
        self.username = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        
        if not all([self.server, self.database, self.username, self.password]):
            raise ValueError("Credenciais de banco de dados incompletas. Verifique o arquivo .env")
        
        # Ajuste para SQL Server: Se tiver porta com ':', troca por ','
        # Isso garante compatibilidade se o usuário colocar IP:PORTA no .env
        if ":" in self.server:
            self.server = self.server.replace(":", ",")

        # Codifica os parâmetros para URL (segurança contra caracteres especiais na senha)
        params = urllib.parse.quote_plus(
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )

        # String de conexão SQLAlchemy usando o formato 'mssql+pyodbc:///?odbc_connect=...'
        self.connection_string = f"mssql+pyodbc:///?odbc_connect={params}"
        
        self.engine = None

    def get_engine(self):
        """Retorna a engine SQLAlchemy (Singleton)."""
        if self.engine is None:
            try:
                self.engine = create_engine(self.connection_string)
            except Exception as e:
                print(f"Erro ao criar engine de banco de dados: {e}")
                raise
        return self.engine

    def get_dataframe(self, query: str, params: dict = None) -> pd.DataFrame:
        """
        Executa uma query SQL e retorna um DataFrame do Pandas.
        Suporta parâmetros para evitar SQL Injection.
        """
        engine = self.get_engine()
        try:
            with engine.connect() as connection:
                # Se houver parâmetros, usa a sintaxe segura do SQLAlchemy
                if params:
                    df = pd.read_sql(text(query), connection, params=params)
                else:
                    df = pd.read_sql(text(query), connection)
            return df
        except Exception as e:
            print(f"Erro ao executar query: {e}")
            return pd.DataFrame() 

    def execute_query(self, query: str, params: dict = None):
        """Executa uma query sem retorno (INSERT, UPDATE, DELETE)."""
        engine = self.get_engine()
        try:
            with engine.connect() as connection:
                if params:
                    connection.execute(text(query), params)
                else:
                    connection.execute(text(query))
                connection.commit()
        except Exception as e:
            print(f"Erro ao executar comando SQL: {e}")
            raise
