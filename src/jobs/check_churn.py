import sys
import os
import argparse
from datetime import datetime

# Adiciona diretório raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connector import DatabaseConnector
from src.services.notification_service import send_notification_to_user

# Configuração
CHURN_THRESHOLD_DAYS = 30
VENDOR_DEFAULT_USER_ID = "V.vp - Renata Rodrigues" # Temporário: Em prod, buscaria o ID do vendedor na tabela

def check_churn_risk():
    """
    Verifica clientes que atingiram exatamente 30 dias sem compras hoje
    e envia notificação para o vendedor responsável.
    """
    print(f"[{datetime.now()}] Iniciando verificação de Churn...")
    
    db = DatabaseConnector()
    
    # Query: Busca clientes cuja última compra foi há EXATAMENTE 30 dias
    # Isso evita spam diário. O alerta é único no dia crítico.
    query = """
    SELECT 
        Codigo_Cliente,
        MAX(Nome_Cliente) as Nome_Cliente,
        MAX(Vendedor_Atual) as Vendedor,
        MAX(Data_Emissao) as Ultima_Compra,
        DATEDIFF(day, MAX(Data_Emissao), GETDATE()) as Dias_Inativo
    FROM FAL_IA_Dados_Vendas_Televendas
    GROUP BY Codigo_Cliente
    HAVING DATEDIFF(day, MAX(Data_Emissao), GETDATE()) = :days
    """
    
    try:
        df = db.get_dataframe(query, params={"days": CHURN_THRESHOLD_DAYS})
        
        if df.empty:
            print(f"Nenhum cliente atingiu {CHURN_THRESHOLD_DAYS} dias de inatividade hoje.")
            return

        print(f"Encontrados {len(df)} clientes em risco crítico.")
        
        count_sent = 0
        for _, row in df.iterrows():
            customer_name = row['Nome_Cliente']
            customer_code = row['Codigo_Cliente']
            vendor_name = row['Vendedor']
            
            # TODO: Mapear 'vendor_name' do SQL para 'user_id' do App.
            # Por enquanto, usamos o hardcoded se o vendedor for a Renata, ou logamos aviso.
            target_user_id = VENDOR_DEFAULT_USER_ID 
            
            # Se tivermos autenticação real futura, faríamos a busca do user_id correto.
            # if vendor_name != target_user_id: continue 
            
            title = "⚠️ Risco de Churn Identificado"
            body = f"O cliente {customer_name} ({customer_code}) completou 30 dias sem compras. Ligue agora!"
            
            # Envia notificacao
            if send_notification_to_user(target_user_id, title, body, data={"cardCode": customer_code}):
                print(f"Notificação enviada para {target_user_id} sobre {customer_code}")
                count_sent += 1
            else:
                print(f"Falha ao notificar {target_user_id} (Token não encontrado?)")
                
        print(f"Job finalizado. {count_sent} notificações enviadas.")
        
    except Exception as e:
        print(f"Erro ao executar job: {e}")

if __name__ == "__main__":
    check_churn_risk()
