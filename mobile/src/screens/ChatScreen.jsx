import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sendChatMessage } from '../services/api';
import { create } from 'twrnc';
import { MaterialIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Tailwind Config
const tw = create(require('../../tailwind.config.js'));

const STORAGE_KEY = '@mariia_chat_history';

export default function ChatScreen({ navigation }) {
    const [messages, setMessages] = useState([
        { id: 1, text: "Olá! Sou a Mari, sua assistente de vendas da Fantástico Alimentos. 🌾\n\nPosso ajudar você a analisar vendas de arroz, feijão e macarrão, ou encontrar oportunidades de recuperação de clientes. O que vamos fazer hoje?", sender: 'bot', time: '09:42' }
    ]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const flatListRef = useRef(null);
    const insets = useSafeAreaInsets();

    // Carrega histórico ao iniciar
    useEffect(() => {
        loadHistory();
    }, []);

    // Salva histórico sempre que mudar
    useEffect(() => {
        if (messages.length > 1) {
            saveHistory();
        }
    }, [messages]);

    // Configura botão de Nova Conversa no Header
    useEffect(() => {
        navigation.setOptions({
            headerRight: () => (
                <TouchableOpacity onPress={confirmNewChat} style={tw`mr-4`}>
                    <MaterialIcons name="delete-outline" size={24} color="white" />
                </TouchableOpacity>
            ),
        });
    }, [navigation]);

    const loadHistory = async () => {
        try {
            const jsonValue = await AsyncStorage.getItem(STORAGE_KEY);
            if (jsonValue != null) {
                setMessages(JSON.parse(jsonValue));
            }
        } catch (e) {
            console.error("Erro ao carregar histórico", e);
        }
    };

    const saveHistory = async () => {
        try {
            const jsonValue = JSON.stringify(messages);
            await AsyncStorage.setItem(STORAGE_KEY, jsonValue);
        } catch (e) {
            console.error("Erro ao salvar histórico", e);
        }
    };

    const confirmNewChat = () => {
        if (Platform.OS === 'web') {
            if (window.confirm("Deseja apagar o histórico e iniciar uma nova conversa?")) {
                startNewChat();
            }
        } else {
            Alert.alert(
                "Nova Conversa",
                "Deseja apagar o histórico e iniciar uma nova conversa?",
                [
                    { text: "Cancelar", style: "cancel" },
                    { text: "Sim, limpar", onPress: startNewChat, style: 'destructive' }
                ]
            );
        }
    };

    const startNewChat = async () => {
        const initialMsg = [{
            id: Date.now(),
            text: "Olá! Sou a Mari, sua assistente de vendas da Fantástico Alimentos. 🌾\n\nPosso ajudar você a analisar vendas de arroz, feijão e macarrão, ou encontrar oportunidades de recuperação de clientes. O que vamos fazer hoje?",
            sender: 'bot',
            time: getCurrentTime()
        }];
        setMessages(initialMsg);
        try {
            await AsyncStorage.removeItem(STORAGE_KEY);
        } catch (e) {
            console.error("Erro ao limpar histórico", e);
        }
    };

    const getCurrentTime = () => {
        const now = new Date();
        return now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    };

    const handleSend = async () => {
        if (!inputText.trim()) return;

        const userMsg = { id: Date.now(), text: inputText, sender: 'user', time: getCurrentTime() };
        setMessages(prev => [...prev, userMsg]);
        setInputText('');
        setLoading(true);

        try {
            const result = await sendChatMessage(userMsg.text, messages);
            const botMsg = {
                id: Date.now() + 1,
                text: result.response || "Desculpe, não entendi.",
                sender: 'bot',
                time: getCurrentTime()
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            const errorMsg = { id: Date.now() + 1, text: "Erro de conexão.", sender: 'bot', time: getCurrentTime() };
            setMessages(prev => [...prev, errorMsg]);
        }
        setLoading(false);
    };

    const handleKeyPress = (e) => {
        if (Platform.OS === 'web' && e.nativeEvent.key === 'Enter' && !e.nativeEvent.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const renderItem = ({ item }) => {
        const isUser = item.sender === 'user';
        return (
            <View style={tw`flex-row ${isUser ? 'flex-row-reverse' : ''} items-end gap-2 mb-6 px-4`}>

                {/* Avatar */}
                {!isUser ? (
                    <View style={tw`w-8 h-8 rounded-full bg-orange-500 justify-center items-center shadow-sm mb-1`}>
                        {/* Fallback to simple color since linear gradient requires another lib, trying simple brand color */}
                        <MaterialIcons name="smart-toy" size={16} color="white" />
                    </View>
                ) : (
                    <View style={tw`w-8` /* Spacer for alignment if needed, or remove */} />
                )}

                <View style={tw`flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%]`}>
                    <Text style={tw`text-[10px] text-gray-400 mb-1 mx-1`}>
                        {isUser ? `Você • ${item.time || ''}` : `Mari IA • ${item.time || ''}`}
                    </Text>

                    <View style={tw`
                        p-3.5 rounded-2xl shadow-sm
                        ${isUser
                            ? 'bg-brand-navy rounded-br-none'
                            : 'bg-white dark:bg-surface-dark border border-gray-100 dark:border-gray-700 rounded-bl-none'
                        }
                    `}>
                        <Text style={tw`text-[15px] leading-relaxed ${isUser ? 'text-white' : 'text-gray-800 dark:text-gray-200'}`}>
                            {item.text}
                        </Text>
                    </View>
                </View>
            </View>
        );
    };

    return (
        <KeyboardAvoidingView
            style={tw`flex-1 bg-gray-50 dark:bg-black`}
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 80}
        >
            {/* Date Pill Placeholder - Static for now */}
            <View style={tw`items-center py-4`}>
                <View style={tw`bg-gray-200 dark:bg-gray-800 px-3 py-1 rounded-full`}>
                    <Text style={tw`text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider`}>Hoje</Text>
                </View>
            </View>

            <FlatList
                ref={flatListRef}
                data={messages}
                keyExtractor={item => item.id.toString()}
                renderItem={renderItem}
                contentContainerStyle={tw`pb-4`}
                onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
                showsVerticalScrollIndicator={false}
            />

            {/* Input Area */}
            <View style={[
                tw`bg-white dark:bg-surface-dark border-t border-gray-200 dark:border-gray-800 p-3 pb-8 shadow-lg`,
                { paddingBottom: Platform.OS === 'ios' ? insets.bottom : 20 }
            ]}>
                <View style={tw`flex-row items-end gap-2 max-w-lg mx-auto w-full`}>
                    <TouchableOpacity style={tw`p-2.5 rounded-full bg-gray-50 hover:bg-gray-100 items-center justify-center`}>
                        <MaterialIcons name="add-circle-outline" size={24} color="#64748B" />
                    </TouchableOpacity>

                    <View style={tw`flex-1 bg-gray-100 dark:bg-gray-800 rounded-2xl border border-transparent focus:border-brand-navy`}>
                        <TextInput
                            style={tw`w-full text-base px-4 py-3 text-gray-800 dark:text-white max-h-24`}
                            value={inputText}
                            onChangeText={setInputText}
                            placeholder="Digite sua mensagem..."
                            placeholderTextColor="#94A3B8"
                            multiline={true}
                            onKeyPress={handleKeyPress}
                        />
                    </View>

                    <TouchableOpacity
                        style={tw`p-3 bg-brand-orange rounded-xl shadow-sm items-center justify-center`}
                        onPress={handleSend}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator size="small" color="white" />
                        ) : (
                            <MaterialIcons name="send" size={20} color="white" />
                        )}
                    </TouchableOpacity>
                </View>
            </View>
        </KeyboardAvoidingView>
    );
}
