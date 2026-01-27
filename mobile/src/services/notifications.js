import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import api from './api';

// Configuração do Handler (o que fazer quando receber notificação com app aberto)
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
    }),
});

export async function registerForPushNotificationsAsync() {
    let token;

    if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.MAX,
            vibrationPattern: [0, 250, 250, 250],
            lightColor: '#FF231F7C',
        });
    }

    if (Device.isDevice) {
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;

        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }

        if (finalStatus !== 'granted') {
            console.log('Permissão de notificação negada!');
            return;
        }

        // Pega o token do Expo Push
        try {
            const projectId = Constants?.expoConfig?.extra?.eas?.projectId ?? Constants?.easConfig?.projectId;
            token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
            console.log("Expo Push Token:", token);
        } catch (e) {
            console.error("Erro ao pegar token Expo:", e);
        }
    } else {
        // console.log('Simulador não suporta Push Notifications físico, mas funciona para emulação parcial.');
    }

    return token;
}

export async function sendTokenToBackend(token) {
    if (!token) return;

    // TODO: Pegar User ID real. Por enquanto usa hardcoded "Default" ou passa como param.
    // O backend usa "Vendor" como ID. Vamos assumir um padrão ou passar parametro.
    const userId = "V.vp - Renata Rodrigues"; // Mudar isso quando tiver login real

    try {
        await api.post('/notifications/register-token', {
            token: token,
            user_id: userId
        });
        console.log("Token enviado para o backend com sucesso.");
    } catch (error) {
        console.error("Erro ao enviar token para backend:", error);
    }
}
