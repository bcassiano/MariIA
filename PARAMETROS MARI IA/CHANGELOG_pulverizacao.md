# Registro de Mudanças - Pulverização de Produtos no Pitch

## 📅 Data: 2026-02-07

## 🎯 Objetivo da Mudança

Ajustar o prompt de geração de pitch para **priorizar a pulverização de produtos com foco em volume de vendas**, reduzindo a concentração excessiva em itens recorrentes e aumentando a diversificação do mix de produtos sugeridos.

---

## ✅ Alterações Implementadas

### 1. Arquivo Modificado
- **Arquivo**: [`telesales_agent.py`](file:///c:/Projetos/MariIA/src/agents/telesales_agent.py#L929-L956)
- **Método**: `generate_pitch()`
- **Linhas**: 929-956

### 2. Mudanças no Prompt

#### ANTES ❌
```python
4. **Pedido Ideal**: Sugira 2 a 4 SKUs. 
   Inclua ITENS RECORRENTES (que ele sempre compra) 
   e 1 OPORTUNIDADE (um item do Top Selling que ele NÃO comprou recentemente).
```

**Problema**: 
- Foco excessivo em produtos recorrentes
- Apenas 1 item de oportunidade (25% do pedido)
- Sem critério de volume ou pulverização

---

#### DEPOIS ✅
```python
4. **Pedido Ideal (ESTRATÉGIA DE PULVERIZAÇÃO - PRIORIDADE MÁXIMA)**: 
   Sugira 3 a 5 SKUs seguindo esta HIERARQUIA OBRIGATÓRIA:
   
   a) **1 Item Âncora** (20-30% da quantidade): 
      O SKU recorrente principal do cliente (giro garantido).
   
   b) **2-3 Itens de Pulverização** (50-60% da quantidade - FOCO PRINCIPAL):
      - Selecione produtos do Top Selling que o cliente NÃO comprou nos últimos 60 dias
      - PRIORIZE itens com MAIOR VOLUME de vendas da empresa (>3.000 unidades/mês)
      - DIVERSIFIQUE categorias (se compra Arroz, sugira Feijão + Massas + Óleo)
      - Foque em produtos com alta rotatividade e giro rápido garantido
   
   c) **1 Item Estratégico** (10-20% - Opcional):
      - Produto premium, lançamento ou margem superior
      - Justifique o valor agregado
   
   REGRA CRÍTICA: Pelo menos 60% da QUANTIDADE TOTAL deve vir de SKUs de categorias 
   DIFERENTES das recorrentes do cliente. Priorize PULVERIZAÇÃO com VOLUME.
```

**Benefícios**:
✅ Diversificação obrigatória de categorias (60% mínimo)  
✅ Foco em produtos de alto volume (>3.000 unidades/mês)  
✅ Hierarquia clara: 1 âncora + 2-3 pulverização + 1 estratégico  
✅ Redução de risco de concentração para o cliente  
✅ Aumento de ticket médio esperado  

---

### 3. Ajuste nos "Reasons" (Transparência)

#### ANTES ❌
```python
- Título: "Oportunidade" | Ícone: "trending_up" | 
  Conteúdo: Por que ele deve comprar o item novo sugerido 
  (ex: é o mais vendido da cia).
```

---

#### DEPOIS ✅
```python
- Título: "Oportunidade de Mix" | Ícone: "trending_up" | 
  Conteúdo: Explicar QUANTITATIVAMENTE o VOLUME de vendas dos produtos 
  de pulverização sugeridos (ex: "Feijão Preto vendeu 15.000 unidades 
  no último trimestre, com crescimento de 25% na região. 
  Diversificar seu mix garante giro rápido e reduz risco de concentração").
```

**Benefícios**:
✅ Justificativa quantitativa (dados de volume)  
✅ Ênfase em giro rápido e redução de risco  
✅ Foco em diversificação estratégica  

---

### 4. Ajuste na Motivação

#### ANTES ❌
```python
6. **Motivação**: Uma frase curta no campo `motivation` que resuma a estratégia 
   (ex: "Reposição de estoque + Oportunidade de Mix").
```

---

#### DEPOIS ✅
```python
6. **Motivação**: Uma frase curta no campo `motivation` que resuma a 
   estratégia de PULVERIZAÇÃO 
   (ex: "Mix estratégico: 1 âncora + 3 categorias de alto volume").
```

---

## 📊 Comparação de Resultados Esperados

### Exemplo Prático: Cliente que compra apenas Arroz

#### ANTES (Concentração) ❌
```json
{
  "suggested_order": [
    {"product_name": "Arroz Branco 5kg", "sku": "0005", "quantity": 30},
    {"product_name": "Arroz Parboilizado 5kg", "sku": "0006", "quantity": 20},
    {"product_name": "Feijão Carioca 1kg", "sku": "0012", "quantity": 10}
  ]
}
```
- **Categorias**: 2 (Arroz, Feijão)
- **% Arroz**: 83% (50/60 unidades)
- **Pulverização**: Baixa
- **Risco**: Cliente dependente de 1 categoria

---

#### DEPOIS (Pulverização) ✅
```json
{
  "suggested_order": [
    {"product_name": "Arroz Branco 5kg", "sku": "0005", "quantity": 20},
    {"product_name": "Feijão Preto 1kg", "sku": "0013", "quantity": 25},
    {"product_name": "Macarrão Espaguete 500g", "sku": "0025", "quantity": 30},
    {"product_name": "Óleo de Soja 900ml", "sku": "0041", "quantity": 15},
    {"product_name": "Açúcar Cristal 1kg", "sku": "0050", "quantity": 10}
  ],
  "motivation": "Mix estratégico: 1 âncora + 4 categorias de alto volume",
  "reasons": [
    {
      "title": "Timing Ideal",
      "text": "Última compra há 18 dias, média de 15 dias. Risco de ruptura moderado.",
      "icon": "history"
    },
    {
      "title": "Giro Garantido",
      "text": "Arroz Branco é seu item âncora, representa 60% do histórico.",
      "icon": "star"
    },
    {
      "title": "Oportunidade de Mix",
      "text": "Feijão Preto (15.000 un/trimestre), Macarrão (22.000 un/trimestre) e Óleo (18.000 un/trimestre) são top performers com crescimento de 25% na região. Diversificar garante giro rápido e reduz risco de concentração em arroz.",
      "icon": "trending_up"
    }
  ]
}
```
- **Categorias**: 5 (Arroz, Feijão, Massas, Óleos, Açúcar)
- **% Arroz**: 20% (20/100 unidades)
- **% Pulverização**: 80%
- **Benefícios**: Mix diversificado, giro garantido, volume alto

---

## 🎯 Parâmetros Críticos Implementados

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| **Quantidade de SKUs** | 3-5 | Diversificação sem sobrecarregar |
| **% Mínimo de Pulverização** | 60% | Força diversificação |
| **Volume Mínimo (sugerido)** | >3.000 un/mês | Garante giro rápido |
| **Período de "Não Comprou"** | 60 dias | Evita sugerir produtos recém-comprados |
| **Item Âncora** | 1 obrigatório | Garante aceitação base |
| **Itens de Pulverização** | 2-3 obrigatórios | Foco principal da mudança |
| **Item Estratégico** | 0-1 opcional | Margem/Premium |

---

## 📈 Métricas de Sucesso Esperadas

| Métrica | Antes | Meta Depois | Prazo |
|---------|-------|-------------|-------|
| **Média de Categorias/Pedido** | 2.1 | 3.5+ | 30 dias |
| **% Pulverização** | 25% | 60%+ | 30 dias |
| **Ticket Médio** | R$ 1.200 | R$ 1.500+ | 60 dias |
| **Taxa de Aceitação** | 75% | 70%+ (manter) | 30 dias |
| **Mix de Produtos (cliente)** | 3.2 SKUs únicos | 5.0+ SKUs únicos | 90 dias |

---

## ⚠️ Riscos e Monitoramento

### Riscos Identificados

1. **Rejeição de Produtos Novos**
   - **Risco**: Cliente pode rejeitar muitos SKUs desconhecidos
   - **Mitigação**: Manter 1 item âncora garantido
   - **Monitorar**: Taxa de aceitação por semana

2. **Redução de Volume por SKU**
   - **Risco**: Pulverização pode reduzir quantidade de cada item
   - **Mitigação**: Critério de volume (>3.000 un/mês) garante giro
   - **Monitorar**: Volume total por pedido

3. **Incompatibilidade de Perfil**
   - **Risco**: Sugerir produtos fora do perfil do cliente
   - **Mitigação**: IA deve respeitar categoria compatível (prompt menciona)
   - **Monitorar**: Feedback dos vendedores

---

### Plano de Monitoramento

```python
# Adicionar ao sistema de logging
log_pitch_usage(
    card_code=card_code,
    pitch_id=pitch_id,
    metadata={
        "num_skus": len(suggested_order),
        "num_categories": count_unique_categories(suggested_order),
        "pulverization_percentage": calculate_pulverization(suggested_order, hist),
        "total_value": sum(sku["quantity"] * sku["unit_price"] for sku in suggested_order)
    }
)
```

---

## 🔄 Próximos Passos

### Fase 1 (Concluída) ✅
- [x] Ajustar prompt em `telesales_agent.py`
- [x] Documentar mudanças
- [x] Criar plano de implementação

### Fase 2 (A Fazer - Sprint 2)
- [ ] Implementar função `get_volume_insights()` para dados quantitativos de volume
- [ ] Adicionar validação de pulverização na resposta (60% mínimo)
- [ ] Testar com 10 clientes piloto e coletar feedback

### Fase 3 (A Fazer - Sprint 3)
- [ ] Dashboard de métricas de pulverização
- [ ] A/B test: prompt antigo vs novo (50/50 split)
- [ ] Ajustes finos baseados em dados reais

---

## 📚 Arquivos Relacionados

- [`telesales_agent.py`](file:///c:/Projetos/MariIA/src/agents/telesales_agent.py) - Código modificado
- [`implementation_plan_pulverizacao.md`](file:///c:/Projetos/MariIA/PARAMETROS%20MARI%20IA/implementation_plan_pulverizacao.md) - Plano detalhado
- [`insights_pitch_parametrizado.md`](file:///c:/Projetos/MariIA/PARAMETROS%20MARI%20IA/insights_pitch_parametrizado.md) - Análise inicial

---

## ✍️ Aprovação e Rollback

### Como Testar
```bash
# Backend
cd c:\Projetos\MariIA
.\run_backend.ps1

# Teste manual via API
curl -X POST http://localhost:8000/pitch \
  -H "Content-Type: application/json" \
  -d '{"card_code": "C002416", "target_sku": ""}'
```

### Rollback (se necessário)
```bash
git checkout src/agents/telesales_agent.py
# Ou reverter apenas as linhas 929-956 manualmente
```

---

**Implementado por**: Bruno Cassiano (via Mari IA Agent)  
**Data**: 2026-02-07 14:24  
**Versão**: 1.0  
**Status**: ✅ IMPLEMENTADO - Aguardando Testes
