import json
import os
import requests
from typing import List, Dict

TOKENS_FILE = os.path.join(os.path.dirname(__file__), '../database/tokens.json')

def load_tokens() -> Dict[str, str]:
    """Carrega o mapeamento user_id -> token do arquivo JSON."""
    if not os.path.exists(TOKENS_FILE):
        return {}
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_token(user_id: str, token: str):
    """Salva ou atualiza o token de um usuário."""
    tokens = load_tokens()
    tokens[user_id] = token
    
    # Garante que o diretório existe
    os.makedirs(os.path.dirname(TOKENS_FILE), exist_ok=True)
    
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)
    print(f"Token salvo para {user_id}: {token}")

def get_token(user_id: str) -> str:
    """Retorna o token de um usuário ou None."""
    tokens = load_tokens()
    return tokens.get(user_id)

def send_push_notification(token: str, title: str, body: str, data: dict = None) -> bool:
    """Envia notificação via Expo Push API."""
    if not token:
        print("Token vazio. Notificação cancelada.")
        return False
        
    url = "https://exp.host/--/api/v2/push/send"
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip, deflate",
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
        "priority": "high"
    }
    
    if data:
        payload["data"] = data
        
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Notificação enviada: {response.json()}")
        return True
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")
        return False

def send_notification_to_user(user_id: str, title: str, body: str, data: dict = None):
    """Envia notificação para um usuário específico pelo ID."""
    token = get_token(user_id)
    if token:
        return send_push_notification(token, title, body, data)
    else:
        print(f"Usuário {user_id} não tem token registrado.")
        return False
