import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Image, Alert } from 'react-native';
import { create } from 'twrnc';
import { AuthService } from '../services/auth';
import { showToast } from '../components/Toast';

const tw = create(require('../../tailwind.config.js'));

export default function LoginScreen({ navigation }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');

    const handleLogin = async () => {
        if (!email || !password) {
            showToast("Por favor, preencha todos os campos.", "error");
            return;
        }

        setLoading(true);
        setLoadingMessage("Autenticando...");
        try {
            await AuthService.login(email, password);
            showToast("Login realizado com sucesso!", "success");
            // App.js listener handles navigation
        } catch (error) {
            console.error("Login Error:", error);
            let msg = "Falha ao entrar.";
            if (error.code === 'auth/invalid-credential') msg = "Credenciais inválidas.";
            if (error.code === 'auth/user-not-found') msg = "Usuário não encontrado.";
            if (error.code === 'auth/wrong-password') msg = "Senha incorreta.";
            if (error.message.includes('E-mail não verificado')) msg = "Por favor, verifique seu e-mail antes de entrar.";

            showToast(msg, "error");
        } finally {
            setLoading(false);
            setLoadingMessage("");
        }
    };

    return (
        <View style={tw`flex-1 bg-white p-6 justify-center`}>
            <View style={tw`items-center mb-10`}>
                <Image
                    source={require('../../assets/logo_fantastico.png')} // Certifique-se que existe ou use placeholder
                    style={tw`w-24 h-24 mb-4`}
                    resizeMode="contain"
                />
                <Text style={tw`text-2xl font-bold text-primary`}>Mari IA</Text>
                <Text style={tw`text-gray-500`}>Portal de Televendas Inteligente</Text>
            </View>

            <View style={tw`gap-4`}>
                <View>
                    <Text style={tw`text-gray-700 font-medium mb-1`}>E-mail</Text>
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

                <TouchableOpacity
                    style={tw`bg-primary p-4 rounded-xl items-center mt-2 shadow-sm`}
                    onPress={handleLogin}
                    disabled={loading}
                >
                    {loading ? (
                        <View style={tw`flex-row items-center gap-2`}>
                            <ActivityIndicator color="white" />
                            <Text style={tw`text-white font-medium`}>{loadingMessage}</Text>
                        </View>
                    ) : (
                        <Text style={tw`text-white font-bold text-lg`}>Entrar</Text>
                    )}
                </TouchableOpacity>

                <View style={tw`flex-row justify-center mt-4`}>
                    <Text style={tw`text-gray-600`}>Não tem uma conta? </Text>
                    <TouchableOpacity onPress={() => navigation.navigate('Register')}>
                        <Text style={tw`text-blue-600 font-bold`}>Cadastre-se</Text>
                    </TouchableOpacity>
                </View>
            </View>
        </View>
    );
}
