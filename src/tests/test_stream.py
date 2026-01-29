import sys
import os
# import pytest
from fastapi.testclient import TestClient

# Adiciona root ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.api.app import app
from src.core.config import get_settings

client = TestClient(app)
settings = get_settings()

def test_chat_stream_hello():
    """Testa um 'Oi' simples para verificar se o stream retorna chunks e status 200."""
    print("\n--- Teste: Chat Stream Hello ---")
    
    with client.stream("POST", "/chat/stream", json={"message": "Olá, quem é você?", "history": []}, headers={"x-api-key": settings.API_KEY}) as response:
        assert response.status_code == 200
        
        # Consome o stream
        content = ""
        for chunk in response.iter_text():
            print(f"CHUNK: {chunk}", end="")
            content += chunk
            
        assert len(content) > 0
        print(f"\nTotal Content Length: {len(content)}")

def test_chat_function_call():
    """Testa uma pergunta que DEVE acionar uma Tool (Function Call)."""
    print("\n--- Teste: Chat Function Call (Histórico do Cliente) ---")
    
    with client.stream("POST", "/chat/stream", json={"message": "Me mostre o histórico do cliente C00123", "history": []}, headers={"x-api-key": settings.API_KEY}) as response: 
        assert response.status_code == 200
        
        content = ""
        for chunk in response.iter_text():
            print(f"{chunk}", end="")
            content += chunk

    assert len(content) > 0
    print("\nTeste concluído.")

if __name__ == "__main__":
    # Roda manualmente se chamado direto
    try:
        test_chat_stream_hello()
        test_chat_function_call()
        print("\n\n[OK] TODOS OS TESTES PASSARAM!")
    except Exception as e:
        print(f"\n\n[ERRO] NO TESTE: {e}")
