# Plano de Correção - Filtro de Dias Sem Compras

## 🐛 Problema Identificado

### Comportamento Atual (INCORRETO)

**Screenshot mostra:**
- Filtro selecionado: **"30 dias"**
- Modo: **"Em Recuperação"** (clientes inativos)
- Resultados:
  - TANHO FOOD SERVICE: Última compra **13/07/2025** (~207 dias atrás)
  - FERREIRA DISTRIBUIDORA: Última compra **06/05/2025** (~277 dias atrás)  
  - UBADESKLIMP: Última compra **24/09/2024** (~501 dias atrás)

**Problema**: Ao selecionar "30 dias", usuário espera ver clientes que **não compram há ~30 dias**, mas está vendo clientes que não compram há **200+, 300+, 500+ dias**.

---

## 🔍 Análise do Código

### Frontend: `HomeScreen.jsx` (Linhas 39-76)

```javascript
const loadData = async (filter, mode) => {
    let minDays, maxDays;
    
    if (filter.min !== undefined) {
        // Range específico (Ex: 15-25)
        minDays = filter.min;
        maxDays = filter.max;
    } else {
        // Padrão (30/60/90)
        if (mode === 'active') {
            minDays = 0;
            maxDays = filter.val;
        } else {
            minDays = filter.val;      // ❌ PROBLEMA AQUI
            maxDays = 9999;            // ❌ PROBLEMA AQUI
        }
    }
    
    // ...
    if (mode === 'active') {
        result = await getInsights(minDays, maxDays);
    } else {
        result = await getInactiveCustomers(minDays, maxDays);
    }
}
```

**Lógica Atual (INCORRETA):**
- Filtro **"30 dias"** em modo **"Em Recuperação"**:
  - `minDays = 30`
  - `maxDays = 9999`
  - Busca clientes que não compram entre 30 e 9999 dias

**Lógica Esperada (CORRETA):**
- Filtro **"30 dias"** deveria buscar clientes que não compram há **aproximadamente 30 dias**
- Range sugerido: 25-35 dias (±5 dias de tolerância)

---

### Backend: `telesales_agent.py` (Linhas 619-652)

```python
def get_inactive_customers(self, min_days: int = 30, max_days: int = 365, vendor_filter: str = None):
    query = f"""
    WITH Base_Inativos AS (
        SELECT 
            Codigo_Cliente,
            MAX(Data_Emissao) as Ultima_Compra
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE 1=1 {vendor_clause}
        GROUP BY Codigo_Cliente
        HAVING MAX(Data_Emissao) < DATEADD(day, -{min_days}, GETDATE())
           AND MAX(Data_Emissao) >= DATEADD(day, -{max_days}, GETDATE())
    )
    SELECT * FROM Base_Inativos ORDER BY Ultima_Compra DESC
    """
```

**Interpretação da Query:**
- `MAX(Data_Emissao) < DATEADD(day, -30, GETDATE())`: Última compra ANTES de 30 dias atrás
- `MAX(Data_Emissao) >= DATEADD(day, -9999, GETDATE())`: Última compra DEPOIS de 9999 dias atrás

**Resultado**: Clientes que compraram entre 30 e 9999 dias atrás (ou seja, todos os inativos de 30+ dias)

---

## ✅ Solução Proposta

### Estratégia 1: Ranges Fixos por Filtro (Recomendada)

Cada filtro deve ter um **range específico** de dias sem compras:

| Filtro | Significado | minDays | maxDays | Range de Inatividade |
|--------|-------------|---------|---------|----------------------|
| **15-25** | Inativos entre 15-25 dias | 15 | 25 | 15 a 25 dias |
| **26-30** | Inativos entre 26-30 dias | 26 | 30 | 26 a 30 dias |
| **30** | Inativos há ~30 dias | **25** | **35** | 25 a 35 dias |
| **60** | Inativos há ~60 dias | **50** | **70** | 50 a 70 dias |
| **90** | Inativos há ~90 dias | **80** | **100** | 80 a 100 dias |

**Vantagens:**
- ✅ Cada filtro mostra um segmento específico de clientes
- ✅ Evita overlap entre filtros
- ✅ UX mais previsível

---

### Estratégia 2: Range Acumulativo (Alternativa)

| Filtro | minDays | maxDays | Range de Inatividade |
|--------|---------|---------|----------------------|
| **30** | 0 | 30 | 0 a 30 dias (todos os inativos até 30 dias) |
| **60** | 0 | 60 | 0 a 60 dias (todos os inativos até 60 dias) |
| **90** | 0 | 90 | 0 a 90 dias (todos os inativos até 90 dias) |

**Vantagens:**
- ✅ Mostra volume total de inativos no período
- ❌ Pode ser confuso (overlap entre filtros)

---

## 🛠️ Implementação

### Opção 1: Ajuste Simples no Frontend (Range com ±10 dias)

**Arquivo**: `mobile/src/screens/HomeScreen.jsx`

```javascript
// ANTES (linhas 51-57)
if (mode === 'active') {
    minDays = 0;
    maxDays = filter.val;
} else {
    minDays = filter.val;
    maxDays = 9999;
}

// DEPOIS
if (mode === 'active') {
    minDays = 0;
    maxDays = filter.val;
} else {
    // Para inativos, criar range de ±10 dias
    const tolerance = 10;
    minDays = Math.max(0, filter.val - tolerance);
    maxDays = filter.val + tolerance;
}
```

**Resultado:**
- Filtro **"30 dias"**: Busca clientes inativos entre **20-40 dias**
- Filtro **"60 dias"**: Busca clientes inativos entre **50-70 dias**
- Filtro **"90 dias"**: Busca clientes inativos entre **80-100 dias**

---

### Opção 2: Ranges Customizados (Mais Preciso)

**Arquivo**: `mobile/src/screens/HomeScreen.jsx`

```javascript
const filters = [
    { label: '15-25', min: 15, max: 25 },
    { label: '26-30', min: 26, max: 30 },
    { label: '30', val: 30, inactiveMin: 25, inactiveMax: 35 },   // ← NOVO
    { label: '60', val: 60, inactiveMin: 50, inactiveMax: 70 },   // ← NOVO
    { label: '90', val: 90, inactiveMin: 80, inactiveMax: 100 }   // ← NOVO
];

// Na função loadData:
if (mode === 'active') {
    minDays = 0;
    maxDays = filter.val;
} else {
    // Usar ranges customizados para inativos
    minDays = filter.inactiveMin || filter.val;
    maxDays = filter.inactiveMax || (filter.val + 10);
}
```

---

## 📋 Checklist de Implementação

### Fase 1: Correção Imediata (Opção 1)
- [ ] Ajustar linha 54-56 de `HomeScreen.jsx`
- [ ] Testar com filtros 30, 60, 90 dias
- [ ] Validar datas das últimas compras

### Fase 2: Refinamento (Opção 2 - Opcional)
- [ ] Adicionar propriedades `inactiveMin` e `inactiveMax` aos filtros
- [ ] Ajustar lógica de loadData
- [ ] Documentar ranges no código

### Fase 3: UX Enhancement (Futuro)
- [ ] Adicionar tooltip explicando o range (ex: "30 dias ≈ 25-35 dias")
- [ ] Mostrar contador de clientes por filtro
- [ ] Adicionar filtro "90+" para inativos de longa data

---

## 🧪 Como Testar

### Teste Manual
1. Reiniciar frontend com a correção
2. Selecionar modo **"Em Recuperação"**
3. Clicar em filtro **"30 dias"**
4. Verificar se a última compra dos clientes está entre **20-40 dias atrás** (data de hoje - 20 a 40 dias)

### Exemplo (Data de hoje: 07/02/2026)
- Filtro **30 dias** deveria mostrar clientes com última compra entre:
  - Mínimo: `07/02/2026 - 40 dias` = **28/12/2025**
  - Máximo: `07/02/2026 - 20 dias` = **18/01/2026**

---

## ⚠️ Impacto

**Alto**: Esta correção muda fundamentalmente o comportamento do filtro. Usuários podem estranhar inicialmente, mas o comportamento correto é mais útil.

**Comunicação necessária**:
> "Ajustamos os filtros de 'Em Recuperação' para mostrar clientes inativos no range específico de dias selecionado (±10 dias), tornando a análise mais precisa."

---

**Criado em**: 2026-02-07  
**Prioridade**: 🔴 ALTA  
**Estimativa**: 15 minutos
