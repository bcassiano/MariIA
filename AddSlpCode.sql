-- 1. Adiciona a coluna SlpCode (Inteiro) se não existir
IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'SlpCode' AND Object_ID = Object_ID(N'FAL_IA_Dados_Vendas_Televendas'))
BEGIN
    ALTER TABLE FAL_IA_Dados_Vendas_Televendas ADD SlpCode INT;
    PRINT 'Coluna SlpCode adicionada com sucesso.';
END
GO

-- 2. Atualiza (Backfill) baseando-se no nome do Vendedor
-- Nota: Assume-se que 'Vendedor_Atual' contém o nome exato.
UPDATE T1
SET T1.SlpCode = T2.SlpCode
FROM FAL_IA_Dados_Vendas_Televendas T1
INNER JOIN OSLP T2 ON T1.Vendedor_Atual COLLATE SQL_Latin1_General_CP1_CI_AS = T2.SlpName COLLATE SQL_Latin1_General_CP1_CI_AS
WHERE T1.SlpCode IS NULL;

PRINT 'SlpCode atualizado para registros existentes.';
