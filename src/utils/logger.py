import json
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "pitch_usage.jsonl")

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def log_pitch_usage(card_code: str, target_sku: str, pitch_generated: str, pitch_id: str, user_id: str = None, metadata: dict = None):
    """
    Registra o uso do Pitch IA em um arquivo JSON Lines.
    """
    ensure_log_dir()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "pitch_generated",
        "pitch_id": pitch_id,
        "user_id": user_id,
        "card_code": card_code,
        "target_sku": target_sku,
        "pitch_generated": pitch_generated,
        "metadata": metadata or {}
    }
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Erro ao gravar log: {e}")

def log_pitch_feedback(pitch_id: str, feedback_type: str, user_id: str = None):
    """
    Registra feedback do usuário sobre o pitch.
    """
    ensure_log_dir()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "pitch_feedback",
        "pitch_id": pitch_id,
        "user_id": user_id,
        "feedback_type": feedback_type # 'useful' | 'sold'
    }
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Erro ao gravar log de feedback: {e}")
