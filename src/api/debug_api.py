import sys
import os
# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.api.app import get_insights

print("Testando get_insights()...")
try:
    result = get_insights(days=30)
    print("Sucesso!")
    print(result)
except Exception as e:
    print(f"ERRO CAPTURADO: {e}")
    import traceback
    traceback.print_exc()
