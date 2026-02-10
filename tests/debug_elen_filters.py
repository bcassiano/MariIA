"""
Script para debugar os filtros de clientes inativos da vendedora Elen.
Verifica a distribuição de clientes por range de dias sem compras.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connector import DatabaseConnector
from datetime import datetime, timedelta

db = DatabaseConnector()

# Vendedora Elen
vendor_name = "Elen"

print(f"\n{'='*80}")
print(f"ANÁLISE DE CLIENTES INATIVOS - {vendor_name}")
print(f"Data de Referência: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(f"{'='*80}\n")

# Ranges de teste
ranges = [
    ("15-25 dias", 15, 25),
    ("26-30 dias", 26, 30),
    ("20-40 dias (30±10)", 20, 40),
    ("50-70 dias (60±10)", 50, 70),
    ("80-100 dias (90±10)", 80, 100),
    ("30-365 dias (30+)", 30, 365),
    ("60-365 dias (60+)", 60, 365),
    ("90-365 dias (90+)", 90, 365),
]

for label, min_days, max_days in ranges:
    query = f"""
    SELECT 
        COUNT(DISTINCT Codigo_Cliente) as Total_Clientes,
        MIN(DATEDIFF(day, MAX(Data_Emissao), GETDATE())) as Dias_Min,
        MAX(DATEDIFF(day, MAX(Data_Emissao), GETDATE())) as Dias_Max,
        AVG(DATEDIFF(day, MAX(Data_Emissao), GETDATE())) as Dias_Media
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Vendedor_Atual = '{vendor_name}'
    GROUP BY Codigo_Cliente
    HAVING MAX(Data_Emissao) < DATEADD(day, -{min_days}, GETDATE())
       AND MAX(Data_Emissao) >= DATEADD(day, -{max_days}, GETDATE())
    """
    
    df = db.get_dataframe(query)
    
    if not df.empty:
        total = df['Total_Clientes'].sum()
        dias_min = df['Dias_Min'].min() if not df['Dias_Min'].isna().all() else 0
        dias_max = df['Dias_Max'].max() if not df['Dias_Max'].isna().all() else 0
        dias_media = df['Dias_Media'].mean() if not df['Dias_Media'].isna().all() else 0
        
        print(f"📊 {label:30} → {total:3} clientes")
        if total > 0:
            print(f"   └─ Inatividade real: {dias_min:.0f} a {dias_max:.0f} dias (média: {dias_media:.0f})")
    else:
        print(f"📊 {label:30} → 0 clientes")
    print()

# Distribuição geral de clientes inativos (30+ dias)
print(f"\n{'='*80}")
print(f"DISTRIBUIÇÃO DETALHADA (30+ dias)")
print(f"{'='*80}\n")

query = """
SELECT 
    Codigo_Cliente,
    MAX(Nome_Cliente) as Nome_Cliente,
    MAX(Data_Emissao) as Ultima_Compra,
    DATEDIFF(day, MAX(Data_Emissao), GETDATE()) as Dias_Sem_Compra
FROM FAL_IA_Dados_Vendas_Televendas
WHERE Vendedor_Atual = 'Elen'
GROUP BY Codigo_Cliente
HAVING MAX(Data_Emissao) < DATEADD(day, -30, GETDATE())
ORDER BY Dias_Sem_Compra ASC
"""

df = db.get_dataframe(query)

if not df.empty:
    print(f"Total de clientes inativos (30+ dias): {len(df)}\n")
    
    # Agrupa por faixas
    faixas = [
        ("30-40 dias", 30, 40),
        ("41-60 dias", 41, 60),
        ("61-90 dias", 61, 90),
        ("91-120 dias", 91, 120),
        ("121+ dias", 121, 9999)
    ]
    
    for label, min_d, max_d in faixas:
        count = len(df[(df['Dias_Sem_Compra'] >= min_d) & (df['Dias_Sem_Compra'] <= max_d)])
        print(f"  {label:15} → {count:3} clientes")
    
    print(f"\n{'='*80}")
    print(f"PRIMEIROS 10 CLIENTES INATIVOS (ordenados por menos tempo)")
    print(f"{'='*80}\n")
    
    for idx, row in df.head(10).iterrows():
        print(f"{row['Codigo_Cliente']:10} | {row['Nome_Cliente'][:40]:40} | {row['Dias_Sem_Compra']:3} dias | Última: {row['Ultima_Compra'].strftime('%d/%m/%Y')}")
else:
    print("Nenhum cliente inativo encontrado para Elen (30+ dias)")

print(f"\n{'='*80}\n")
