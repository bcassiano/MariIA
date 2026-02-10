# Análise do Problema - Filtros de Clientes Inativos

## 🐛 Situação Reportada

**Usuário**: Apenas o filtro **"15-25 dias"** traz resultados de clientes em recuperação da vendedora Elen.

**Filtros que NÃO retornam dados:**
- 26-30 dias
- 30 dias  
- 60 dias
- 90 dias

---

## 🔍 Análise da Causa Raiz

### Filtro 15-25 (Funciona) ✅

```javascript
// HomeScreen.jsx - linha 45
if (filter.min !== undefined) {
    // Range específico (Ex: 15-25)
    minDays = filter.min;        // 15
    maxDays = filter.max;        // 25
}
```

**Query gerada:**
```sql
HAVING MAX(Data_Emissao) < DATEADD(day, -15, GETDATE())     -- Última compra ANTES de 15 dias atrás
   AND MAX(Data_Emissao) >= DATEADD(day, -25, GETDATE())    -- Última compra DEPOIS de 25 dias atrás
```

**Resultado**: Clientes com última compra entre 15-25 dias atrás ✅

---

### Filtro 30 dias (Não funciona após correção) ❌

**ANTES da minha correção:**
```javascript
minDays = filter.val;    // 30
maxDays = 9999;          // 9999
```
**Query antiga**:
```sql
HAVING MAX(Data_Emissao) < DATEADD(day, -30, GETDATE())     
   AND MAX(Data_Emissao) >= DATEADD(day, -9999, GETDATE())
```
**Resultado**: TODOS os clientes inativos de 30+ dias (muito amplo, mas funcionava)

---

**DEPOIS da minha correção:**
```javascript
const tolerance = 10;
minDays = Math.max(0, filter.val - tolerance);   // 20
maxDays = filter.val + tolerance;                // 40
```
**Query nova**:
```sql
HAVING MAX(Data_Emissao) < DATEADD(day, -20, GETDATE())     
   AND MAX(Data_Emissao) >= DATEADD(day, -40, GETDATE())
```
**Resultado**: Apenas clientes com última compra entre 20-40 dias atrás

---

## 🎯 Problema Identificado

A vendedora **Elen** provavelmente **NÃO TEM** clientes inativos nos ranges:
- 20-40 dias (filtro 30)
- 50-70 dias (filtro 60)  
- 80-100 dias (filtro 90)

**Hipótese**: Elen tem apenas clientes que:
1. **Estão ativos** (compraram recentemente)
2. **Estão no range 15-25 dias** (em recuperação recente)
3. **Estão muito inativos** (100+, 200+ dias)

A minha correção **eliminou** a possibilidade de ver clientes **muito inativos** (100+, 200+ dias) ao selecionar "30", "60" ou "90 dias".

---

## ✅ Soluções Propostas

### Opção 1: Reverter para Lógica Antiga (Range Acumulativo) [RECOMENDADA]

**Justificativa**: A lógica antiga de "30 dias = 30+ (todos os inativos de 30 ou mais))" era mais útil na prática, apesar de menos precisa conceitualmente.

```javascript
// HomeScreen.jsx
if (mode === 'active') {
    // Positivados: últimos X dias
    minDays = 0;
    maxDays = filter.val;
} else {
    // Em Recuperação: X dias ou mais (range acumulativo)
    minDays = filter.val;
    maxDays = 9999;
}
```

**Vantagens:**
- ✅ Garante que sempre haverá resultados (se existirem inativos)
- ✅ Usuário consegue ver TODOS os inativos de 30+ dias
- ✅ Filtros mais amplos (60, 90) mostram subconjuntos

**Desvantagens:**
- ❌ Overlap entre filtros (30 dias mostra mesmos clientes que 60 dias)
- ❌ Não é intuitivo (usuário pode esperar "exatamente 30 dias")

---

### Opção 2: Adicionar Filtro "30+" para Clientes Muito Inativos

Manter a lógica de range (±10 dias) mas adicionar filtros específicos para longa inatividade:

```javascript
const filters = [
    { label: '15-25', min: 15, max: 25 },
    { label: '26-30', min: 26, max: 30 },
    { label: '30', val: 30, inactiveMin: 20, inactiveMax: 40 },
    { label: '60', val: 60, inactiveMin: 50, inactiveMax: 70 },
    { label: '90', val: 90, inactiveMin: 80, inactiveMax: 100 },
    { label: '90+', min: 90, max: 9999 }  // ← NOVO: Muito inativos
];
```

**Vantagens:**
- ✅ Melhor granularidade
- ✅ Filtro "90+" captura todos os esquecidos
- ✅ Ranges específicos para análise detalhada

---

### Opção 3: UX Dinâmico (Fallback Automático)

Se um filtro não retornar resultados, expandir automaticamente o range:

```javascript
// Pseudo-código
let result = await getInactiveCustomers(minDays, maxDays);
if (result.data.length === 0 && mode === 'inactive') {
    // Tenta novamente com range mais amplo
    result = await getInactiveCustomers(minDays, 9999);
}
```

**Vantagens:**
- ✅ Sempre mostra dados relevantes
- ❌ Complexidade adicional
- ❌ Pode confundir o usuário

---

## 🎯 Recomendação Final

**Reverter para a lógica antiga (Opção 1)** + **adicionar tooltip explicativo**:

```javascript
// Em modo "Em Recuperação":
minDays = filter.val;
maxDays = 9999;
```

**Com tooltip:**
```
"30 dias" = Clientes sem compras há 30 dias ou mais
"60 dias" = Clientes sem compras há 60 dias ou mais  
"90 dias" = Clientes sem compras há 90 dias ou mais
```

**Ou:**

**Manter a nova lógica mas adicionar filtro "90+"** (Opção 2):
- Filtros 15-25, 26-30: ranges fixos
- Filtros 30, 60, 90: ranges ±10 dias
- Filtro **90+**: captura todos os muito inativos

---

## 📝 Decisão do Cliente

**Qual opção prefere?**

1. **Reverter** para "30 dias = 30+ (todos os inativos de 30 ou mais)"
2. **Manter** a nova lógica (ranges específicos) e **adicionar filtro "90+"**
3. **Ajustar** o tolerance de ±10 para ±20 dias (ranges maiores)

---

**Data**: 2026-02-07  
**Urgência**: Alta (bloqueando uso do filtro)
