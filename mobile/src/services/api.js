import axios from 'axios';
import { Platform } from 'react-native';

// Define a URL base dependendo do dispositivo
// Prod: Cloud Run
// const API_URL = 'https://mariia-backend-635293407607.us-central1.run.app';
// Dev Local (IP da sua máquina)
const API_URL = 'http://192.168.0.21:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'x-api-key': process.env.EXPO_PUBLIC_API_KEY || 'mariia-secret-key-123'
    }
});

export const getInsights = async (minDays = 0, maxDays = 30) => {
    try {
        console.log(`Chamando API em: ${API_URL}/insights?min_days=${minDays}&max_days=${maxDays}`);
        const response = await api.get(`/insights?min_days=${minDays}&max_days=${maxDays}`);
        return response.data;
    } catch (error) {
        console.error("Erro ao buscar insights:", error);
        // Retorna o erro para ser exibido na tela
        return { data: [], error: error.message + (error.response ? ` (${error.response.status})` : "") };
    }
};

export const getInactiveCustomers = async (minDays = 30, maxDays = 365) => {
    try {
        console.log(`Chamando API em: ${API_URL}/inactive?min_days=${minDays}&max_days=${maxDays}`);
        const response = await api.get(`/inactive?min_days=${minDays}&max_days=${maxDays}`);
        return response.data;
    } catch (error) {
        console.error("Erro ao buscar inativos:", error);
        return { error: error.message };
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

export const generatePitch = async (cardCode, targetSku, userId = "vendedor_mobile") => {
    try {
        const response = await api.post('/pitch', {
            card_code: cardCode,
            target_sku: targetSku,
            user_id: userId
        });
        return response.data;
    } catch (error) {
        console.error("Erro ao gerar pitch:", error);
        return { pitch: "Erro ao conectar com a IA." };
    }
};

export const sendPitchFeedback = async (pitchId, feedbackType, userId = "vendedor_mobile") => {
    try {
        await api.post('/pitch/feedback', {
            pitch_id: pitchId,
            feedback_type: feedbackType,
            user_id: userId
        });
        return true;
    } catch (error) {
        console.error("Erro ao enviar feedback:", error);
        return false;
    }
};

export const sendChatMessage = async (message, history = []) => {
    try {
        const response = await api.post('/chat', { message, history });
        return response.data;
    } catch (error) {
        console.error("Erro no chat:", error);
        return { response: "Erro ao conectar com a IA." };
    }
};

export default api;
