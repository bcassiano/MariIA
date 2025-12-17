USE [RUSTON_PRODUCAO]
GO

/****** Object:  View [dbo].[FAL_IA_Dados_Vendas_Televendas]    Script Date: 16/12/2025 14:30:00 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

ALTER   VIEW [dbo].[FAL_IA_Dados_Vendas_Televendas] AS

/*
    VIEW: IA_Dados_Vendas_Televendas
    OBJETIVO: Fornecer dados consolidados e performáticos para agentes de IA (Televendas).
    CONTEÚDO: Faturas, Pedidos em Aberto, Entregas, Devoluções e Cotações.
    OTIMIZAÇÕES:
    1. Remoção de Subqueries Correlacionadas (Fatores, Frete).
    2. Filtro de Data SARGable (Index Seek).
    3. Nomes de colunas em PT-BR padronizados.
    4. Pré-cálculo de Margem e Lucro.
    
    ATUALIZAÇÃO (16/12/2025):
    - Inclusão da coluna 'Vendedor_Atual' baseada no cadastro do Cliente (OCRD), 
      permitindo filtrar a carteira atual independente do histórico de vendas.
*/

WITH Fatores AS (
    -- CTE para carregar Fatores de Custo e Despesa uma única vez por Ano/Mês
    SELECT 
        T101.Name AS Ano,
        T100.U_Mes AS Mes,
        MAX(T100.U_CUSTO) AS Fator_Custo,
        MAX(T100.U_DESPESA) AS Fator_Despesa
    FROM [@RAL_FATORES] T100 
    INNER JOIN [@RAL_FATORESANO] T101 ON T101.Code = T100.U_Ano
    GROUP BY T101.Name, T100.U_Mes
)

SELECT 
    -- Identificação do Documento
    A.Tipo_Documento,
    A.Numero_Documento,
    A.Numero_NF,
    A.Data_Emissao,
    A.Data_Entrega_Prometida,
    A.Status_Documento,
    
    -- Cliente e Vendedor
    A.Codigo_Cliente,
    A.Nome_Cliente,
    A.Grupo_Cliente,
    A.Tipo_Cliente,
    A.Cidade,
    A.Estado,
    A.Regiao,
    A.Macro_Regiao,
    A.Vendedor,       -- Vendedor que emitiu a nota (Histórico)
    A.Vendedor_Atual, -- [NOVO] Vendedor dono da carteira (Atual)
    A.Supervisor,
    A.Equipe_Vendas,
    A.Area_Atuacao,

    -- Produto
    A.SKU,
    A.Nome_Produto,
    A.Grupo_Produto,
    A.Categoria_Produto,
    A.Marca,
    A.Utilizacao,
    A.Unidade_Medida,
    
    -- Quantidades e Pesos
    A.Quantidade,
    A.Peso_KG,
    
    -- Valores Monetários (Unitários e Totais)
    A.Preco_Lista,
    A.Preco_Unitario_Original, -- Sem desconto
    A.Valor_Total_Linha,       -- Valor Bruto da Linha
    A.Percentual_Desconto,
    A.Valor_Desconto,
    A.Valor_Liquido,           -- Valor Linha - Desconto
    
    -- Custos e Margens (Calculados)
    A.Custo_Estoque_Unitario,
    A.Custo_Total_Estoque,
    
    -- Cálculos de Negócio (Fatores Aplicados)
    A.Fator_Custo_Aplicado,
    A.Fator_Despesa_Aplicado,
    
    CAST(A.Custo_Total_Estoque * (1 + ISNULL(A.Fator_Custo_Aplicado, 0)) AS DECIMAL(18,2)) AS Custo_Final_Com_Fator,
    
    CAST(A.Valor_Liquido + A.Valor_Imposto - (A.Custo_Total_Estoque * (1 + ISNULL(A.Fator_Custo_Aplicado, 0))) AS DECIMAL(18,2)) AS Lucro_Bruto,
    
    -- Margem Líquida Estimada
    CAST(
        (A.Valor_Liquido + A.Valor_Imposto - (A.Custo_Total_Estoque * (1 + ISNULL(A.Fator_Custo_Aplicado, 0)))) -- Lucro Bruto
        - (ISNULL(A.Valor_Comissao, 0) + (A.Valor_Liquido * ISNULL(A.Fator_Despesa_Aplicado, 0))) -- Despesas Comerciais
        - ISNULL(A.Valor_Frete, 0) -- Frete
    AS DECIMAL(18,2)) AS Margem_Valor,

    -- Impostos e Extras
    A.Valor_Imposto,
    A.Valor_Frete,
    A.Percentual_Comissao,
    A.Valor_Comissao

FROM (

    -- 1. FATURAS (VENDAS EFETIVAS)
    SELECT 
        'Fatura' AS Tipo_Documento,
        T0.DocNum AS Numero_Documento,
        T0.DocNum AS Numero_NF,
        T0.DocDate AS Data_Emissao,
        dbo.DataPrometidaPedido(T0.DocEntry, T1.LineNum) AS Data_Entrega_Prometida,
        CASE WHEN T0.Canceled = 'Y' THEN 'Cancelado' ELSE 'Faturado' END AS Status_Documento,
        
        T5.CardCode AS Codigo_Cliente,
        T5.CardName AS Nome_Cliente,
        T7.GroupName AS Grupo_Cliente,
        T24.INDname AS Tipo_Cliente,
        T19.Name AS Cidade,
        T6.State AS Estado,
        T18.GroupName AS Regiao,
        T9.Name AS Macro_Regiao,
        T8.SlpName AS Vendedor,
        T_Carteira.SlpName AS Vendedor_Atual, -- [NOVO]
        T16.firstName AS Supervisor,
        CAST(T28.name AS VARCHAR) AS Equipe_Vendas,
        T26.Name AS Area_Atuacao,

        T2.ItemCode AS SKU,
        T2.ItemName AS Nome_Produto,
        T3.ItmsGrpNam AS Grupo_Produto,
        T17.Name AS Categoria_Produto,
        T2.U_Marca AS Marca,
        T4.Usage AS Utilizacao,
        T1.UnitMsr AS Unidade_Medida,

        T1.Quantity AS Quantidade,
        CASE WHEN (T1.Quantity * T11.Weight1) = 0 THEN (T1.Quantity * T2.SWeight1) ELSE (T1.Quantity * T11.Weight1) END AS Peso_KG,

        T1.U_PrecoDeLista AS Preco_Lista,
        T1.Price AS Preco_Unitario_Original,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) END AS Valor_Total_Linha,
        T5.U_MW_DESFIN AS Percentual_Desconto,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) END AS Valor_Desconto,
        (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) END) - (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) END) AS Valor_Liquido,

        T1.StockPrice AS Custo_Estoque_Unitario,
        (T1.StockPrice * T1.Quantity) AS Custo_Total_Estoque,

        -- Join com CTE de Fatores
        F.Fator_Custo AS Fator_Custo_Aplicado,
        F.Fator_Despesa AS Fator_Despesa_Aplicado,

        CASE WHEN T3.ItmsGrpNam = 'PA FEIJÃO' THEN ROUND(T1.LineTotal, 2) * -0.01 ELSE T14.TaxSum * -1 END AS Valor_Imposto,
        
        -- Lógica Simplificada de Frete
        CASE 
            WHEN T30.Incoterms IN (1, 9) THEN 0 
            ELSE ( (ISNULL(T23.U_Valor_Total_Frete, 0) / NULLIF(T23.U_Peso_Estimado - T23.U_Peso_Estimado_Pallets, 0)) * (CASE WHEN (T1.Quantity * T11.Weight1) = 0 THEN (T1.Quantity * T2.SWeight1) ELSE (T1.Quantity * T11.Weight1) END) )
        END AS Valor_Frete,

        T13.U_MW_PRCT AS Percentual_Comissao,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T13.U_MW_PRCT / 100) END AS Valor_Comissao

    FROM INV4 T14
    INNER JOIN OINV T0 ON T0.DocEntry = T14.DocEntry
    INNER JOIN INV1 T1 ON T0.DocEntry = T1.DocEntry AND T1.LineNum = T14.LineNum
    INNER JOIN INV12 T30 ON T0.DocEntry = T30.DocEntry
    LEFT JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
    INNER JOIN OUOM T11 ON T11.UomCode = T1.UomCode
    LEFT JOIN OCRD T5 ON T0.CardCode = T5.CardCode
    LEFT JOIN OSLP T_Carteira ON T_Carteira.SlpCode = T5.SlpCode -- [NOVO] Join com a carteira atual (Cadastro)
    LEFT JOIN OUSG T4 ON T1.Usage = T4.ID
    LEFT JOIN OSLP T8 ON T8.SlpCode = T0.SlpCode
    LEFT JOIN CRD1 T6 ON T6.CardCode = T5.CardCode AND T6.Address = 'FATURAMENTO'
    LEFT JOIN OCRG T7 ON T7.GroupCode = T5.GroupCode
    LEFT JOIN OITB T3 ON T3.ItmsGrpCod = T2.ItmsGrpCod
    LEFT JOIN [@MW_MACRO] T9 ON T9.Code = T5.U_MW_MACRO
    LEFT JOIN [@MW_CDV0] T12 ON T8.SlpName = T12.U_MW_SlpCode
    LEFT JOIN [@MW_CDV1] T13 ON T12.Code = T13.Code AND T2.ItemCode = T13.U_MW_ItemCode
    LEFT JOIN OHEM T15 ON T15.salesPrson = T8.SlpCode
    LEFT JOIN OHEM T16 ON T16.empID = T15.manager
    LEFT JOIN [@CATPROD] T17 ON T17.Code = T2.U_CATPROD
    LEFT JOIN OCQG T18 ON T18.GroupCode = CASE WHEN T5.QryGroup1 = 'Y' THEN 1 ELSE 0 END
    INNER JOIN OCNT T19 ON T6.County = T19.AbsId
    LEFT JOIN [@BIM_ORDEMCARGA] T23 ON T1.U_OC_num = T23.DocEntry
    LEFT JOIN OOND T24 ON T24.INDCODE = T5.INDUSTRYC
    LEFT JOIN [@RAL_AREAATUCAO] T26 ON T26.Code = T5.U_AreaAtuacao
    LEFT JOIN HTM1 T27 ON T27.empID = T15.empID
    LEFT JOIN OHTM T28 ON T28.teamID = T27.teamID
    LEFT JOIN Fatores F ON F.Ano = DATEPART(YEAR, T0.DocDate) AND F.Mes = DATEPART(MONTH, T0.DocDate)

    WHERE T14.staType IN (25, 31) 
      AND T0.Canceled = 'N' 
      AND T14.TaxStatus = 'Y' 
      AND T0.DocStatus IN ('O', 'C')
      AND T1.CFOPCODE IN ('5101','5102','5123','5122','5118','5201','5551','5910','6101','6102','6108','6120','6910','6122','6551','7101','7102','7501','6501','5949')
      AND T0.DocDate >= DATEADD(YEAR, -4, GETDATE())

    UNION ALL

    -- 2. PEDIDOS EM ABERTO
    SELECT 
        'Pedido' AS Tipo_Documento,
        T0.DocNum AS Numero_Documento,
        NULL AS Numero_NF,
        T0.DocDate AS Data_Emissao,
        T0.DocDueDate AS Data_Entrega_Prometida,
        'Aberto' AS Status_Documento,
        
        T5.CardCode, T5.CardName, T7.GroupName, T24.INDname, T19.Name, T6.State, T18.GroupName, T9.Name, T8.SlpName, 
        T_Carteira.SlpName AS Vendedor_Atual, -- [NOVO]
        T16.firstName, T28.name, T26.Name,
        T2.ItemCode, T2.ItemName, T3.ItmsGrpNam, T17.Name, T2.U_Marca, T4.Usage, T1.UnitMsr,
        
        T1.OpenQty AS Quantidade,
        CASE WHEN (T1.OpenQty * T11.Weight1) = 0 THEN (T1.OpenQty * T2.SWeight1) ELSE (T1.OpenQty * T11.Weight1) END AS Peso_KG,
        
        T1.U_PrecoDeLista, T1.Price,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) END,
        T5.U_MW_DESFIN,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) END,
        (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) END) - (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) END),
        
        T1.StockPrice, (T1.StockPrice * T1.OpenQty),
        
        F.Fator_Custo, F.Fator_Despesa,
        
        CASE WHEN T3.ItmsGrpNam = 'PA FEIJÃO' THEN ROUND(T1.LineTotal, 2) * -0.01 ELSE T14.TaxSum * -1 END,
        
        0 AS Valor_Frete, 
        
        T13.U_MW_PRCT,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T13.U_MW_PRCT / 100) END

    FROM RDR4 T14
    INNER JOIN ORDR T0 ON T0.DocEntry = T14.DocEntry
    INNER JOIN RDR1 T1 ON T0.DocEntry = T1.DocEntry AND T1.LineNum = T14.LineNum
    INNER JOIN RDR12 T30 ON T0.DocEntry = T30.DocEntry
    INNER JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
    INNER JOIN OUOM T11 ON T11.UomCode = T1.UomCode
    INNER JOIN OCRD T5 ON T5.CardCode = T0.CardCode
    LEFT JOIN OSLP T_Carteira ON T_Carteira.SlpCode = T5.SlpCode -- [NOVO]
    LEFT JOIN CRD1 T6 ON T6.CardCode = T5.CardCode AND T6.Address = 'FATURAMENTO'
    LEFT JOIN OSLP T8 ON T0.SlpCode = T8.SlpCode
    LEFT JOIN OCRG T7 ON T7.GroupCode = T5.GroupCode
    INNER JOIN OUSG T4 ON T4.ID = T1.Usage
    LEFT JOIN OITB T3 ON T3.ItmsGrpCod = T2.ItmsGrpCod
    LEFT JOIN [@MW_MACRO] T9 ON T9.Code = T5.U_MW_MACRO
    LEFT JOIN [@MW_CDV0] T12 ON T8.SlpName = T12.U_MW_SlpCode
    LEFT JOIN [@MW_CDV1] T13 ON T12.Code = T13.Code AND T2.ItemCode = T13.U_MW_ItemCode
    LEFT JOIN OHEM T15 ON T15.salesPrson = T8.SlpCode
    LEFT JOIN OHEM T16 ON T16.empID = T15.manager
    LEFT JOIN [@CATPROD] T17 ON T17.Code = T2.U_CATPROD
    LEFT JOIN OCQG T18 ON T18.GroupCode = CASE WHEN T5.QryGroup1 = 'Y' THEN 1 ELSE 0 END
    INNER JOIN OCNT T19 ON T6.County = T19.AbsId
    LEFT JOIN OOND T24 ON T24.INDCODE = T5.INDUSTRYC
    LEFT JOIN [@RAL_AREAATUCAO] T26 ON T26.Code = T5.U_AreaAtuacao
    LEFT JOIN HTM1 T27 ON T27.empID = T15.empID
    LEFT JOIN OHTM T28 ON T28.teamID = T27.teamID
    LEFT JOIN Fatores F ON F.Ano = DATEPART(YEAR, T0.DocDate) AND F.Mes = DATEPART(MONTH, T0.DocDate)

    WHERE T14.staType IN (25, 31) 
      AND T0.DocStatus = 'O' 
      AND T14.TaxStatus = 'Y' 
      AND T1.OpenQty > 0
      AND T0.DocDate >= DATEADD(YEAR, -4, GETDATE())

    UNION ALL

    -- 3. COTAÇÕES
    SELECT 
        'Cotacao' AS Tipo_Documento,
        T0.DocNum AS Numero_Documento,
        NULL AS Numero_NF,
        T0.DocDate AS Data_Emissao,
        T0.DocDueDate AS Data_Entrega_Prometida,
        'Aberto' AS Status_Documento,
        
        T5.CardCode, T5.CardName, T7.GroupName, T24.INDname, T19.Name, T6.State, T18.GroupName, T9.Name, T8.SlpName, 
        T_Carteira.SlpName AS Vendedor_Atual, -- [NOVO]
        T16.firstName, T28.name, T26.Name,
        T2.ItemCode, T2.ItemName, T3.ItmsGrpNam, T17.Name, T2.U_Marca, T4.Usage, T1.UnitMsr,
        
        T1.OpenQty AS Quantidade,
        CASE WHEN (T1.OpenQty * T11.Weight1) = 0 THEN (T1.OpenQty * T2.SWeight1) ELSE (T1.OpenQty * T11.Weight1) END AS Peso_KG,
        
        T1.U_PrecoDeLista, T1.Price,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.OpenQty * T1.Price, 2) END,
        T5.U_MW_DESFIN,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.OpenQty * T1.Price, 2) * (T5.U_MW_DESFIN / 100)) END,
        (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.OpenQty * T1.Price, 2) END) - (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.OpenQty * T1.Price, 2) * (T5.U_MW_DESFIN / 100)) END),
        
        T1.StockPrice, (T1.StockPrice * T1.OpenQty),
        
        F.Fator_Custo, F.Fator_Despesa,
        
        CASE WHEN T3.ItmsGrpNam = 'PA FEIJÃO' THEN ROUND(T1.LineTotal, 2) * -0.01 ELSE T14.TaxSum * -1 END,
        0 AS Valor_Frete,
        T13.U_MW_PRCT,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T13.U_MW_PRCT / 100) END

    FROM QUT4 T14
    INNER JOIN OQUT T0 ON T0.DocEntry = T14.DocEntry
    INNER JOIN QUT1 T1 ON T0.DocEntry = T1.DocEntry AND T1.LineNum = T14.LineNum
    INNER JOIN QUT12 T30 ON T0.DocEntry = T30.DocEntry
    INNER JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
    INNER JOIN OUOM T11 ON T11.UomCode = T1.UomCode
    INNER JOIN OCRD T5 ON T5.CardCode = T0.CardCode
    LEFT JOIN OSLP T_Carteira ON T_Carteira.SlpCode = T5.SlpCode -- [NOVO]
    LEFT JOIN CRD1 T6 ON T6.CardCode = T5.CardCode AND T6.Address = 'FATURAMENTO'
    LEFT JOIN OSLP T8 ON T0.SlpCode = T8.SlpCode
    LEFT JOIN OCRG T7 ON T7.GroupCode = T5.GroupCode
    INNER JOIN OUSG T4 ON T4.ID = T1.Usage
    LEFT JOIN OITB T3 ON T3.ItmsGrpCod = T2.ItmsGrpCod
    LEFT JOIN [@MW_MACRO] T9 ON T9.Code = T5.U_MW_MACRO
    LEFT JOIN [@MW_CDV0] T12 ON T8.SlpName = T12.U_MW_SlpCode
    LEFT JOIN [@MW_CDV1] T13 ON T12.Code = T13.Code AND T2.ItemCode = T13.U_MW_ItemCode
    LEFT JOIN OHEM T15 ON T15.salesPrson = T8.SlpCode
    LEFT JOIN OHEM T16 ON T16.empID = T15.manager
    LEFT JOIN [@CATPROD] T17 ON T17.Code = T2.U_CATPROD
    LEFT JOIN OCQG T18 ON T18.GroupCode = CASE WHEN T5.QryGroup1 = 'Y' THEN 1 ELSE 0 END
    INNER JOIN OCNT T19 ON T6.County = T19.AbsId
    LEFT JOIN OOND T24 ON T24.INDCODE = T5.INDUSTRYC
    LEFT JOIN [@RAL_AREAATUCAO] T26 ON T26.Code = T5.U_AreaAtuacao
    LEFT JOIN HTM1 T27 ON T27.empID = T15.empID
    LEFT JOIN OHTM T28 ON T28.teamID = T27.teamID
    LEFT JOIN Fatores F ON F.Ano = DATEPART(YEAR, T0.DocDate) AND F.Mes = DATEPART(MONTH, T0.DocDate)

    WHERE T14.staType IN (25, 31) 
      AND T0.DocStatus = 'O' 
      AND T14.TaxStatus = 'Y' 
      AND T1.OpenQty <> 0
      AND T0.DocDate >= DATEADD(YEAR, -4, GETDATE())

    UNION ALL

    -- 4. ENTREGAS EM ABERTO
    SELECT 
        'Entrega' AS Tipo_Documento,
        T0.DocNum AS Numero_Documento,
        T0.DocNum AS Numero_NF,
        T0.DocDate AS Data_Emissao,
        T0.DocDueDate AS Data_Entrega_Prometida,
        'Aberto' AS Status_Documento,
        
        T5.CardCode, T5.CardName, T7.GroupName, T24.INDname, T19.Name, T6.State, T18.GroupName, T9.Name, T8.SlpName, 
        T_Carteira.SlpName AS Vendedor_Atual, -- [NOVO]
        T16.firstName, T28.name, T26.Name,
        T2.ItemCode, T2.ItemName, T3.ItmsGrpNam, T17.Name, T2.U_Marca, T4.Usage, T1.UnitMsr,
        
        T1.Quantity AS Quantidade,
        CASE WHEN (T1.Quantity * T11.Weight1) = 0 THEN (T1.Quantity * T2.SWeight1) ELSE (T1.Quantity * T11.Weight1) END AS Peso_KG,
        
        T1.U_PrecoDeLista, T1.Price,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) END,
        T5.U_MW_DESFIN,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) END,
        (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) END) - (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) END),
        
        T1.StockPrice, (T1.StockPrice * T1.Quantity),
        
        F.Fator_Custo, F.Fator_Despesa,
        
        CASE WHEN T3.ItmsGrpNam = 'PA FEIJÃO' THEN ROUND(T1.LineTotal, 2) * -0.01 ELSE T14.TaxSum * -1 END,
        
        CASE 
            WHEN T30.Incoterms IN (1, 9) THEN 0 
            ELSE ( (ISNULL(T23.U_Valor_Total_Frete, 0) / NULLIF(T23.U_Peso_Estimado - T23.U_Peso_Estimado_Pallets, 0)) * (CASE WHEN (T1.Quantity * T11.Weight1) = 0 THEN (T1.Quantity * T2.SWeight1) ELSE (T1.Quantity * T11.Weight1) END) )
        END AS Valor_Frete,
        
        T13.U_MW_PRCT,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T13.U_MW_PRCT / 100) END

    FROM DLN4 T14
    INNER JOIN ODLN T0 ON T0.DocEntry = T14.DocEntry
    INNER JOIN DLN1 T1 ON T0.DocEntry = T1.DocEntry AND T1.LineNum = T14.LineNum
    INNER JOIN DLN12 T30 ON T0.DocEntry = T30.DocEntry
    LEFT JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
    INNER JOIN OUOM T11 ON T11.UomCode = T1.UomCode
    LEFT JOIN OCRD T5 ON T0.CardCode = T5.CardCode
    LEFT JOIN OSLP T_Carteira ON T_Carteira.SlpCode = T5.SlpCode -- [NOVO]
    LEFT JOIN OUSG T4 ON T1.Usage = T4.ID
    LEFT JOIN OSLP T8 ON T8.SlpCode = T0.SlpCode
    LEFT JOIN CRD1 T6 ON T6.CardCode = T5.CardCode AND T6.Address = 'FATURAMENTO'
    LEFT JOIN OCRG T7 ON T7.GroupCode = T5.GroupCode
    LEFT JOIN OITB T3 ON T3.ItmsGrpCod = T2.ItmsGrpCod
    LEFT JOIN [@MW_MACRO] T9 ON T9.Code = T5.U_MW_MACRO
    LEFT JOIN [@MW_CDV0] T12 ON T8.SlpName = T12.U_MW_SlpCode
    LEFT JOIN [@MW_CDV1] T13 ON T12.Code = T13.Code AND T2.ItemCode = T13.U_MW_ItemCode
    LEFT JOIN OHEM T15 ON T15.salesPrson = T8.SlpCode
    LEFT JOIN OHEM T16 ON T16.empID = T15.manager
    LEFT JOIN [@CATPROD] T17 ON T17.Code = T2.U_CATPROD
    LEFT JOIN OCQG T18 ON T18.GroupCode = CASE WHEN T5.QryGroup1 = 'Y' THEN 1 ELSE 0 END
    INNER JOIN OCNT T19 ON T6.County = T19.AbsId
    LEFT JOIN [@BIM_ORDEMCARGA] T23 ON T1.U_OC_num = T23.DocEntry
    LEFT JOIN OOND T24 ON T24.INDCODE = T5.INDUSTRYC
    LEFT JOIN [@RAL_AREAATUCAO] T26 ON T26.Code = T5.U_AreaAtuacao
    LEFT JOIN HTM1 T27 ON T27.empID = T15.empID
    LEFT JOIN OHTM T28 ON T28.teamID = T27.teamID
    LEFT JOIN Fatores F ON F.Ano = DATEPART(YEAR, T0.DocDate) AND F.Mes = DATEPART(MONTH, T0.DocDate)

    WHERE T14.staType IN (25, 31) 
      AND T0.Canceled = 'N' 
      AND T14.TaxStatus = 'Y' 
      AND T0.DocStatus = 'O'
      AND T0.DocDate >= DATEADD(YEAR, -4, GETDATE())

    UNION ALL

    -- 5. DEVOLUÇÕES
    SELECT 
        'Devolucao' AS Tipo_Documento,
        NULL AS Numero_Documento,
        T0.DocNum AS Numero_NF,
        T0.DocDate AS Data_Emissao,
        NULL AS Data_Entrega_Prometida,
        'Devolvido' AS Status_Documento,
        
        T5.CardCode, T5.CardName, T7.GroupName, T24.INDname, T19.Name, T6.State, T18.GroupName, T9.Name, T8.SlpName, 
        T_Carteira.SlpName AS Vendedor_Atual, -- [NOVO]
        T16.firstName, T31.name, T29.Name,
        T2.ItemCode, T2.ItemName, T3.ItmsGrpNam, T17.Name, T2.U_Marca, CONCAT(T4.Usage, ' - DEV'), T1.UnitMsr,
        
        (T1.Quantity * -1) AS Quantidade,
        CASE WHEN (T1.Quantity * T11.Weight1) = 0 THEN (T1.Quantity * T2.SWeight1) * -1 ELSE (T1.Quantity * T11.Weight1) * -1 END AS Peso_KG,
        
        T1.U_PrecoDeLista, T1.Price,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) * -1 END,
        T5.U_MW_DESFIN,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) * -1 END,
        (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE ROUND(T1.LineTotal, 2) * -1 END) - (CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T5.U_MW_DESFIN / 100) * -1 END),
        
        T1.StockPrice, ((T1.StockPrice * T1.Quantity) * -1),
        
        F.Fator_Custo, F.Fator_Despesa,
        
        CASE WHEN T3.ItmsGrpNam = 'PA FEIJÃO' THEN ROUND(T1.LineTotal, 2) * 0.01 ELSE T14.TaxSum END,
        0 AS Valor_Frete,
        T13.U_MW_PRCT,
        CASE WHEN T1.Usage IN ('13', '52') THEN 0 ELSE (ROUND(T1.LineTotal, 2) * T13.U_MW_PRCT / 100) * -1 END

    FROM RIN4 T14
    INNER JOIN ORIN T0 ON T0.DocEntry = T14.DocEntry
    INNER JOIN RIN1 T1 ON T0.DocEntry = T1.DocEntry AND T1.LineNum = T14.LineNum
    INNER JOIN OUOM T11 ON T11.UomCode = T1.UomCode
    LEFT JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
    LEFT JOIN OCRD T5 ON T0.CardCode = T5.CardCode
    LEFT JOIN OSLP T_Carteira ON T_Carteira.SlpCode = T5.SlpCode -- [NOVO]
    LEFT JOIN OUSG T4 ON T1.Usage = T4.ID
    LEFT JOIN OSLP T8 ON T8.SlpCode = T0.SlpCode
    LEFT JOIN CRD1 T6 ON T6.CardCode = T5.CardCode AND T6.Address = 'FATURAMENTO'
    LEFT JOIN OCRG T7 ON T7.GroupCode = T5.GroupCode
    LEFT JOIN OITB T3 ON T3.ItmsGrpCod = T2.ItmsGrpCod
    LEFT JOIN [@MW_MACRO] T9 ON T9.Code = T5.U_MW_MACRO
    LEFT JOIN [@MW_CDV0] T12 ON T8.SlpName = T12.U_MW_SlpCode
    LEFT JOIN [@MW_CDV1] T13 ON T12.Code = T13.Code AND T2.ItemCode = T13.U_MW_ItemCode
    LEFT JOIN OHEM T15 ON T15.salesPrson = T8.SlpCode
    LEFT JOIN OHEM T16 ON T16.empID = T15.manager
    LEFT JOIN [@CATPROD] T17 ON T17.Code = T2.U_CATPROD
    LEFT JOIN OCQG T18 ON T18.GroupCode = CASE WHEN T5.QryGroup1 = 'Y' THEN 1 ELSE 0 END
    INNER JOIN OCNT T19 ON T6.County = T19.AbsId
    LEFT JOIN OOND T24 ON T24.INDCODE = T5.INDUSTRYC
    LEFT JOIN [@RAL_AREAATUCAO] T29 ON T29.Code = T5.U_AreaAtuacao
    LEFT JOIN HTM1 T30 ON T30.empID = T15.empID
    LEFT JOIN OHTM T31 ON T31.teamID = T30.teamID
    LEFT JOIN Fatores F ON F.Ano = DATEPART(YEAR, T0.DocDate) AND F.Mes = DATEPART(MONTH, T0.DocDate)

    WHERE T14.staType IN (25, 31) 
      AND T14.TaxStatus = 'Y' 
      AND T0.Canceled = 'N' 
      AND T0.DocStatus IN ('O', 'C')
      AND T0.DocDate >= DATEADD(YEAR, -4, GETDATE())

) A;
GO