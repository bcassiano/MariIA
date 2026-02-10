# Plano de Implementação - Pulverização de Produtos no Pitch

## Objetivo

Ajustar o prompt de geração de pitch para priorizar a **pulverização de produtos** (mix diversificado) com foco em **produtos de alto volume** de vendas, evitando concentração excessiva nos mesmos SKUs recorrentes.

---

## Contexto Atual

### Instrução Atual (Linha 933)
```
Pedido Ideal: Sugira 2 a 4 SKUs. Inclua ITENS RECORRENTES (que ele sempre compra) 
e 1 OPORTUNIDADE (um item do Top Selling que ele NÃO comprou recentemente).
```

### Problema Identificado
- Foco excessivo em itens recorrentes
- Apenas 1 item de oportunidade (25% do pedido)
- Não há critério explícito de volume para pulverização
- Falta estratégia de diversificação do mix

---

## Estratégia Proposta

### Nova Abordagem: "Mix Estratégico com Volume"

**Composição do Pedido Ideal (3-5 SKUs):**

1. **1 Item Âncora Recorrente** (20-30%)
   - O SKU de maior recorrência histórica do cliente
   - Garantia de aceitação do pedido

2. **2-3 Itens de Pulverização de Alto Volume** (50-60%)
   - Produtos do Top Selling que o cliente NÃO comprou nos últimos 60 dias
   - Priorizar itens com maior volume de vendas da empresa
   - Categorias complementares ao perfil do cliente

3. **1 Item Estratégico/Premium** (10-20%)
   - Produto com margem superior ou lançamento
   - Oportunidade de upselling

---

## Alterações Propostas

### 1. Prompt de Geração de Pitch

#### Nova Instrução (#4)
```markdown
4. **Pedido Ideal (ESTRATÉGIA DE PULVERIZAÇÃO)**: 
   Sugira 3 a 5 SKUs seguindo esta HIERARQUIA OBRIGATÓRIA:
   
   a) **1 Item Âncora** (Recorrente): O SKU que o cliente mais compra historicamente.
   
   b) **2-3 Itens de Pulverização** (PRIORIDADE MÁXIMA): 
      - Selecione produtos do Top Selling que o cliente NÃO comprou nos últimos 60 dias
      - PRIORIZE itens com MAIOR VOLUME de vendas da empresa
      - Diversifique categorias (se compra só Arroz, sugira Feijão, Massas, Óleo)
      - Foque em produtos com alta rotatividade e giro garantido
   
   c) **1 Item Estratégico** (Opcional): 
      - Produto premium, lançamento ou margem superior
      - Justifique o valor agregado
   
   REGRA CRÍTICA: Pelo menos 60% do valor total do pedido deve vir de 
   itens de PULVERIZAÇÃO (categorias diferentes das recorrentes do cliente).
```

#### Novo Reason (#3 - Oportunidade)
```markdown
- Título: "Oportunidade de Mix" | Ícone: "trending_up" | 
  Conteúdo: Explicar QUANTITATIVAMENTE o volume de vendas dos produtos 
  sugeridos (ex: "Feijão Preto vendeu 15.000 unidades no último trimestre, 
  com crescimento de 25% na região")
```

### 2. Dados Adicionais de Contexto

#### Adicionar ao Prompt:
```python
# Após top_selling, adicionar:
volume_insights = self.get_volume_insights(days=90)  # Nova função

# No prompt:
PRODUTOS DE ALTO VOLUME (ÚLTIMOS 90 DIAS):
{volume_insights}

REGRA: Produtos com volume > 5.000 unidades/mês devem ser PRIORIZADOS 
na pulverização para garantir giro rápido ao cliente.
```

---

## Implementação Técnica

### Fase 1: Ajuste de Prompt (Imediato)

**Arquivo**: `src/agents/telesales_agent.py`

- [ ] Modificar linha 933: Alterar instrução de "Pedido Ideal"
- [ ] Adicionar critérios de pulverização (60% do valor)
- [ ] Enfatizar volume de vendas como critério
- [ ] Ajustar instrução do reason "Oportunidade" (linha 937)

**Mudanças no Prompt:**
```python
# ANTES:
4. **Pedido Ideal**: Sugira 2 a 4 SKUs. Inclua ITENS RECORRENTES (que ele sempre compra) 
   e 1 OPORTUNIDADE (um item do Top Selling que ele NÃO comprou recentemente).

# DEPOIS:
4. **Pedido Ideal (ESTRATÉGIA DE PULVERIZAÇÃO)**: Sugira 3 a 5 SKUs priorizando 
   DIVERSIFICAÇÃO DE CATEGORIAS com foco em PRODUTOS DE ALTO VOLUME.
   
   COMPOSIÇÃO OBRIGATÓRIA:
   - 1 SKU Âncora (recorrente do cliente)
   - 2-3 SKUs de Pulverização (Top Selling que ele NÃO compra, ALTO VOLUME)
   - 1 SKU Estratégico (opcional, premium/lançamento)
   
   CRITÉRIO DE SUCESSO: Pelo menos 60% da quantidade total deve ser de categorias 
   DIFERENTES das que o cliente normalmente compra. Priorize produtos com volume 
   mensal > 3.000 unidades na empresa.
```

### Fase 2: Nova Função de Volume (Opcional - Médio Prazo)

**Arquivo**: `src/agents/telesales_agent.py`

```python
def get_volume_insights(self, days: int = 90) -> str:
    """Retorna produtos de alto volume com métricas quantitativas."""
    query = f"""
    SELECT TOP 15 
        SKU,
        MAX(Nome_Produto) as Produto,
        SUM(Quantidade) as Volume_Total,
        COUNT(DISTINCT Codigo_Cliente) as Clientes_Ativos,
        ROUND(AVG(Valor_Liquido), 2) as Ticket_Medio,
        MAX(Categoria_Produto) as Categoria
    FROM FAL_IA_Dados_Vendas_Televendas 
    WHERE Data_Emissao >= DATEADD(day, -{days}, GETDATE())
    GROUP BY SKU
    HAVING SUM(Quantidade) > 3000  -- Volume mínimo
    ORDER BY Volume_Total DESC
    """
    df = self.db.get_dataframe(query)
    if not df.empty and 'SKU' in df.columns:
        df['SKU'] = df['SKU'].apply(self._format_sku)
    return df.to_markdown(index=False)
```

### Fase 3: Validação de Resposta (Opcional)

**Arquivo**: `src/agents/telesales_agent.py` (após linha 972)

```python
# Validação de pulverização
if 'suggested_order' in data and len(data['suggested_order']) > 0:
    # Verificar se há diversificação de categorias
    # (implementação futura com base em categoria dos produtos)
    pass
```

---

## Exemplo de Saída Esperada

### ANTES (Foco em Recorrentes)
```json
{
  "suggested_order": [
    {"product_name": "Arroz Branco 5kg", "sku": "0005", "quantity": 30},
    {"product_name": "Arroz Parboilizado 5kg", "sku": "0006", "quantity": 20},
    {"product_name": "Feijão Carioca 1kg", "sku": "0012", "quantity": 10}
  ]
}
```
**Problema**: 50 unidades de arroz (83% do pedido) - Sem pulverização

---

### DEPOIS (Pulverização com Volume)
```json
{
  "suggested_order": [
    {"product_name": "Arroz Branco 5kg", "sku": "0005", "quantity": 15, "category": "Arroz"},
    {"product_name": "Feijão Preto 1kg", "sku": "0013", "quantity": 20, "category": "Feijão"},
    {"product_name": "Macarrão Espaguete 500g", "sku": "0025", "quantity": 30, "category": "Massas"},
    {"product_name": "Óleo de Soja 900ml", "sku": "0041", "quantity": 15, "category": "Óleos"},
    {"product_name": "Açúcar Cristal 1kg", "sku": "0050", "quantity": 10, "category": "Açúcar"}
  ],
  "reasons": [
    {
      "title": "Timing Ideal",
      "text": "Última compra há 18 dias, média de reposição de 15 dias.",
      "icon": "history"
    },
    {
      "title": "Giro Garantido",
      "text": "Arroz Branco é seu item âncora (60% do histórico).",
      "icon": "star"
    },
    {
      "title": "Oportunidade de Mix",
      "text": "Feijão Preto e Macarrão Espaguete somam 45.000 unidades/mês na empresa, com crescimento de 30%. Você ainda não experimenta essas categorias que garantem giro rápido.",
      "icon": "trending_up"
    }
  ],
  "motivation": "Mix estratégico: 1 âncora + 4 produtos de alto volume"
}
```
**Resultado**: 5 categorias diferentes, 83% do pedido em pulverização

---

## Métricas de Sucesso

| Métrica | Meta | Como Medir |
|---------|------|------------|
| **Diversificação de Categorias** | Média de 3+ categorias por pedido | `COUNT(DISTINCT categoria)` |
| **% Pulverização** | 60%+ do valor em novos produtos | Soma de SKUs não recorrentes |
| **Volume Total** | Aumento de 20% no ticket médio | Comparar antes/depois |
| **Taxa de Aceitação** | Manter > 70% | Logs de `pitch_usage.jsonl` |

---

## Riscos e Mitigações

> [!WARNING]
> **Risco 1**: Cliente pode rejeitar muitos itens novos de uma vez

**Mitigação**: Manter 1 item âncora (recorrente) para garantir aceitação base

---

> [!CAUTION]
> **Risco 2**: Produtos de alto volume podem não ser adequados ao perfil do cliente

**Mitigação**: Adicionar filtro de categoria compatível (se compra cesta básica, não sugerir premium)

---

## Cronograma

### Sprint 1 (Imediato)
- [x] Documentar plano de implementação
- [ ] Ajustar prompt em `telesales_agent.py` (linhas 933-937)
- [ ] Testar com 5 clientes piloto
- [ ] Validar estrutura de resposta

### Sprint 2 (Semana 2)
- [ ] Implementar `get_volume_insights()`
- [ ] Adicionar contexto de volume ao prompt
- [ ] Criar validação de pulverização na resposta

### Sprint 3 (Semana 3)
- [ ] Dashboard de métricas de pulverização
- [ ] A/B test: prompt antigo vs novo
- [ ] Ajustes finos baseados em feedback

---

## Aprovação Necessária

> [!IMPORTANT]
> **Decisões Estratégicas que Precisam de Validação:**

1. **Proporção de Pulverização**: 60% é adequado ou ajustar para 50%/70%?
2. **Quantidade de SKUs**: 3-5 itens ou manter 2-4?
3. **Threshold de Volume**: 3.000 unidades/mês é o corte ideal?
4. **Categorias Prioritárias**: Há categorias específicas que devem ser enfatizadas?

---

**Criado em**: 2026-02-07  
**Autor**: Bruno Cassiano (via Mari IA Agent)  
**Status**: Aguardando Aprovação
