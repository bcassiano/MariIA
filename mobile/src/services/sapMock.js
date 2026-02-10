/**
 * Simulates checking SAP B1 for a valid salesperson based on their email.
 * In production, this would be a real API call to your backend/SAP Service Layer.
 */
export const MockSapService = {
    getSlpCodeByEmail: async (email) => {
        console.log(`[MockSapService] Buscando SlpCode para: ${email}`);

        // Simulate network delay (500ms - 1.5s)
        const delay = Math.floor(Math.random() * 1000) + 500;
        await new Promise(resolve => setTimeout(resolve, delay));

        // Extract username from email
        // Ex: "bruno.cassiano@fantastico..." -> "bruno.cassiano"
        const username = email.split('@')[0].toLowerCase();

        // ---------------------------------------------------------
        // MOCK DATABASE (Tabela de Vendedores SAP Simulada)
        // ---------------------------------------------------------
        const sapDatabase = {
            'bruno.cassiano': 1,      // Exemplo real
            'elen.hasman': 123,       // Exemplo do prompt
            'vendedor.teste': 99,     // Teste genérico
            'admin': -1,              // Superusuário
            // Adicione novos usuários aqui para testar
        };

        const slpCode = sapDatabase[username];

        if (slpCode !== undefined) {
            console.log(`[MockSapService] Encontrado! SlpCode: ${slpCode}`);
            return slpCode;
        } else {
            console.error(`[MockSapService] Usuário '${username}' não encontrado no SAP.`);
            throw new Error(`Vendedor '${username}' não encontrado na base ativa do SAP.`);
        }
    }
};
