import axios from 'axios';
import { Platform } from 'react-native';

// Define a URL base dependendo do dispositivo
// Web: localhost
// Mobile (Físico/Emulador): IP da sua máquina na rede local
// IMPORTANTE: Se o IP mudar, atualize aqui!
const API_URL = Platform.OS === 'web' ? 'http://localhost:8000' : 'http://192.168.0.55:8000';

const api = axios.create({
    baseURL: API_URL,
});

export const getInsights = async (days = 30) => {
    try {
        console.log(`Chamando API em: ${API_URL}/insights?days=${days}`);
        const response = await api.get(`/insights?days=${days}`);
        return response.data;
    } catch (error) {
        console.error("Erro ao buscar insights:", error);
        // Retorna o erro para ser exibido na tela
        return { data: [], error: error.message + (error.response ? ` (${error.response.status})` : "") };
    }
};

export const getCustomer = async (cardCode) => {
    try {
        const response = await api.get(`/customer/${cardCode}`);
        return response.data;
    } catch (error) {
        console.error("Erro ao buscar cliente:", error);
        return null;
    }
};

export const generatePitch = async (cardCode, targetSku) => {
    try {
        const response = await api.post('/pitch', {
            card_code: cardCode,
            target_sku: targetSku
        });
        return response.data;
    } catch (error) {
        console.error("Erro ao gerar pitch:", error);
        return { pitch: "Erro ao conectar com a IA." };
    }
};

export const sendChatMessage = async (message) => {
    try {
        const response = await api.post('/chat', { message });
        return response.data;
    } catch (error) {
        console.error("Erro no chat:", error);
        return { response: "Erro ao conectar com a IA." };
    }
};

export default api;
