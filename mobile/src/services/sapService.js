import api from './api';

/**
 * Service to interact with SAP Business One data.
 */
export const SapService = {
    /**
     * Retrieves the SAP Sales Person Code (SlpCode) based on the user's email.
     * @param {string} email - User's corporate email
     * @returns {Promise<number>} SlpCode
     */
    getSlpCodeByEmail: async (email) => {
        console.log(`[SapService] Consultando Real SlpCode para: ${email}`);

        try {
            const response = await api.get(`/auth/sap-id?email=${encodeURIComponent(email)}`);

            const { slpCode } = response.data;

            if (slpCode !== null && slpCode !== undefined) {
                console.log(`[SapService] Sucesso! ${email} -> SlpCode ${slpCode}`);
                return slpCode;
            }

            console.warn(`[SapService] Vendedor não encontrado no SAP para: ${email}`);
            throw new Error(`Seu e-mail (${email}) não foi encontrado na base de vendedores do SAP. Verifique se o e-mail está correto.`);
        } catch (error) {
            console.error(`[SapService] Erro na integração SAP:`, error);

            if (error.response?.status === 403) {
                throw new Error("Erro de autenticação com o servidor (API Key).");
            }

            throw error;
        }
    }
};
