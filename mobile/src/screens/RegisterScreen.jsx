import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { create } from 'twrnc';
import { AuthService } from '../services/auth';
import { SapService } from '../services/sapService';
import { showToast } from '../components/Toast';
import Icon from '../components/Icon';

const tw = create(require('../../tailwind.config.js'));

export default function RegisterScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');

    const handleRegister = async () => {
        if (!email || !password) {
            Alert.alert("Erro", "Todos os campos são obrigatórios.");
            return;
        }

        // Domain Validation
        const allowedDomain = "@fantasticoalimentos.com.br";
        if (!email.toLowerCase().endsWith(allowedDomain)) {
            Alert.alert("Acesso Restrito", `Apenas e-mails corporativos (${allowedDomain}) são permitidos.`);
            return;
        }

        if (password !== confirmPassword) {
            Alert.alert("Erro", "As senhas não coincidem.");
            return;
        }

        if (password.length < 6) {
            Alert.alert("Erro", "A senha deve ter pelo menos 6 caracteres.");
            return;
        }

        setLoading(true);
        setLoadingMessage("Mapeando SAP...");
        try {
            // 1. Auto-extract SlpCode (Simulated SAP Call -> Real DB in Future)
            let slpCode = null;
            try {
                slpCode = await SapService.getSlpCodeByEmail(email);
            } catch (sapError) {
                console.warn("Register: User not found in SAP. Proceeding as Pending Authorization.", sapError.message);
                // Allow registration to proceed without SlpCode (handling Pending state later)
            }

            setLoadingMessage("Criando Conta...");
            // 2. Register & Send Verification Email
            await AuthService.register(email, password, slpCode);

            showToast("Conta criada! Verifique seu e-mail.", "success");

            // Poll every 3 seconds
            const intervalId = setInterval(async () => {
                try {
                    await AuthService.login(email, password);
                    // If login succeeds, it means email is verified!
                    clearInterval(intervalId);
                    // App.js listener handles navigation
                } catch (err) {
                    console.log(`[DEBUG] Polling failed: ${err.message}`);
                    // Ignore expected "unverified" errors
                    if (err.message.includes('não verificado')) {
                        console.log("Polling: User exists but still Unverified. Waiting...");
                    } else {
                        console.log("Polling error (unexpected):", err.message);
                    }
                }
            }, 3000);

            // Safety timeout: Stop polling after 2 minutes
            setTimeout(() => clearInterval(intervalId), 120000);

        } catch (error) {
            console.error("Register Error:", error);
            Alert.alert("Erro ao criar conta", error.message);
        } finally {
            // Keep loading true? No, let user interact if needed.
            setLoading(false);
        }
    };

    const checkVerificationManual = async () => {
        setLoading(true);
        try {
            await AuthService.login(email, password);
        } catch (error) {
            Alert.alert("Ainda não verificado", "Por favor, clique no link enviado para seu e-mail.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <ScrollView contentContainerStyle={tw`flex-grow justify-center bg-white p-6`}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={tw`mb-6`}>
                <Text style={tw`text-primary font-bold text-lg`}>← Voltar</Text>
            </TouchableOpacity>

            <Text style={tw`text-3xl font-bold text-primary mb-2`}>Criar Conta</Text>
            <Text style={tw`text-gray-500 mb-8`}>Vincule seu usuário SAP para acessar.</Text>

            <View style={tw`gap-4`}>
                <View>
                    <Text style={tw`text-gray-700 font-medium mb-1`}>E-mail Corporativo</Text>
                    <TextInput
                        style={tw`border border-gray-300 rounded-lg p-3 text-base bg-gray-50`}
                        placeholder="seu@email.com"
                        keyboardType="email-address"
                        autoCapitalize="none"
                        value={email}
                        onChangeText={setEmail}
                    />
                </View>

                <View>
                    <Text style={tw`text-gray-700 font-medium mb-1`}>Senha</Text>
                    <TextInput
                        style={tw`border border-gray-300 rounded-lg p-3 text-base bg-gray-50`}
                        placeholder="••••••••"
                        secureTextEntry
                        value={password}
                        onChangeText={setPassword}
                    />
                </View>

                <View>
                    <Text style={tw`text-gray-700 font-medium mb-1`}>Confirmar Senha</Text>
                    <TextInput
                        style={tw`border border-gray-300 rounded-lg p-3 text-base bg-gray-50`}
                        placeholder="••••••••"
                        secureTextEntry
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                    />
                </View>

                <TouchableOpacity
                    style={tw`bg-primary p-4 rounded-xl items-center mt-4 shadow-sm`}
                    onPress={handleRegister}
                    disabled={loading}
                >
                    {loading ? (
                        <View style={tw`flex-row items-center gap-2`}>
                            <ActivityIndicator color="white" />
                            <Text style={tw`text-white font-medium`}>{loadingMessage}</Text>
                        </View>
                    ) : (
                        <Text style={tw`text-white font-bold text-lg`}>Cadastrar</Text>
                    )}
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}
