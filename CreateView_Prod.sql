USE RUSTON_PRODUCAO;
GO

-- 1. Cria a View segura
CREATE OR ALTER VIEW VW_MariIA_ClientDetails AS
SELECT 
    CardCode,
    CardName,
    CAST(YEAR(CreateDate) as VARCHAR) as AtivoDesde,
    ISNULL(Phone1, Phone2) as Telefone,
    E_Mail as Email,
    Address as Endereco
FROM OCRD
WHERE CardType = 'C';
GO

-- 2. Concede permissão APENAS na View para o usuário 'powerbi'
GRANT SELECT ON VW_MariIA_ClientDetails TO powerbi;
GO

PRINT 'View criada e permissão concedida com sucesso!';
