import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Alert, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sendChatMessage, streamChatMessage } from '../services/api';
import { create } from 'twrnc';
import { MaterialIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import TypingIndicator from '../components/TypingIndicator';
import Markdown from 'react-native-markdown-display';

// Tailwind Config
const tw = create(require('../../tailwind.config.js'));

const STORAGE_KEY = '@mariia_chat_history';

export default function ChatScreen({ navigation }) {
    const [messages, setMessages] = useState([
        { id: 1, text: "Olá! Sou a Mari IA a inteligência Artificial da Fantástico Alimentos. 🌾\n\nPosso ajudar você a analisar vendas de arroz, feijão e macarrão, ou encontrar oportunidades de recuperação de clientes. O que vamos fazer hoje?", sender: 'bot', time: '09:42' }
    ]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const flatListRef = useRef(null);
    const insets = useSafeAreaInsets();
    const abortControllerRef = useRef(null);



    const handleSend = async () => {
        if (!inputText.trim()) return;

        const userMsg = { id: Date.now(), text: inputText, sender: 'user', time: getCurrentTime() };

        // Adiciona mensagem do usuário
        setMessages(prev => [...prev, userMsg]);
        setInputText('');
        setLoading(true);

        // Cancel previous request if any
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        // Create new controller
        abortControllerRef.current = new AbortController();

        // Adiciona placeholder da resposta do Bot IMEDIATAMENTE
        const botMsgId = Date.now() + 1;
        const botMsg = {
            id: botMsgId,
            text: "", // Começa vazio
            sender: 'bot',
            time: getCurrentTime()
        };

        setMessages(prev => [...prev, botMsg]);

        try {
            await streamChatMessage(
                userMsg.text,
                messages.slice(-6), // Envia histórico recente
                (chunk) => {
                    // Update incremental
                    setMessages(prev => {
                        const newMessages = [...prev];
                        const lastMsgIndex = newMessages.findIndex(m => m.id === botMsgId);
                        if (lastMsgIndex !== -1) {
                            newMessages[lastMsgIndex] = {
                                ...newMessages[lastMsgIndex],
                                text: newMessages[lastMsgIndex].text + chunk
                            };
                        }
                        return newMessages;
                    });
                },
                abortControllerRef.current.signal
            );

        } catch (error) {
            if (error.name === 'AbortError' || error.message === 'Canceled') {
                console.log('Request canceled');
            } else {
                setMessages(prev => [...prev, { id: Date.now() + 2, text: "Erro ao processar resposta.", sender: 'bot', time: getCurrentTime() }]);
            }
        } finally {
            setLoading(false);
            abortControllerRef.current = null;
        }
    };

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setLoading(false);
    };



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
            text: "Olá! Sou a Mari IA a inteligência Artificial da Fantástico Alimentos. 🌾\n\nPosso ajudar você a analisar vendas de arroz, feijão e macarrão, ou encontrar oportunidades de recuperação de clientes. O que vamos fazer hoje?",
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
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const handleKeyPress = (e) => {
        if (e.nativeEvent.key === 'Enter' && !e.nativeEvent.shiftKey) {
            handleSend();
        }
    };

    const renderItem = ({ item }) => {
        const isUser = item.sender === 'user';
        return (
            <View style={[
                tw`flex-row mb-4 px-4`,
                isUser ? tw`justify-end` : tw`justify-start`
            ]}>
                {!isUser && (
                    <View style={tw`w-8 h-8 rounded-full bg-white items-center justify-center mr-2 shadow-sm border border-gray-100`}>
                        <Image source={require('../../assets/logo_fantastico.png')} style={{ width: 24, height: 24 }} resizeMode="contain" />
                    </View>
                )}
                <View style={[
                    tw`max-w-[80%] p-4 rounded-2xl shadow-sm`,
                    isUser ? tw`bg-blue-900 rounded-tr-none` : tw`bg-white dark:bg-gray-800 rounded-tl-none`
                ]}>
                    {!isUser && loading && item.text === "" ? (
                        <TypingIndicator />
                    ) : (
                        <View style={isUser ? {} : tw`w-full`}>
                            {/* Renderiza Markdown para mensagens do Bot, Texto simples para User */}
                            {isUser ? (
                                <Text style={tw`text-base text-white leading-relaxed`}>
                                    {item.text}
                                </Text>
                            ) : (
                                <Markdown
                                    style={{
                                        body: { color: '#1F2937', fontSize: 16, lineHeight: 24 },
                                        paragraph: { marginBottom: 10 },
                                        heading3: { fontSize: 18, fontWeight: 'bold', color: '#111827', marginTop: 10, marginBottom: 5 },
                                        code_block: { backgroundColor: '#F3F4F6', padding: 10, borderRadius: 8, fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace', fontSize: 12 },
                                        table: { borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 8, overflow: 'hidden', marginTop: 10 },
                                        tr: { borderBottomWidth: 1, borderColor: '#E5E7EB', flexDirection: 'row' },
                                        th: { padding: 10, backgroundColor: '#F9FAFB', fontWeight: 'bold', color: '#374151' },
                                        td: { padding: 10, color: '#4B5563' },
                                        li: { marginBottom: 5 },
                                    }}
                                >
                                    {item.text}
                                </Markdown>
                            )}
                        </View>
                    )}
                    <Text style={[
                        tw`text-[10px] mt-1 text-right`,
                        isUser ? tw`text-blue-200` : tw`text-gray-400`
                    ]}>
                        {item.time}
                    </Text>
                </View>
            </View>
        );
    };

    return (
        <KeyboardAvoidingView
            style={tw`flex-1 bg-background-light dark:bg-black`}
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
                    {!inputText && !loading && (
                        <TouchableOpacity style={tw`p-2.5 rounded-full bg-gray-50 dark:bg-gray-800 items-center justify-center`}>
                            <MaterialIcons name="add" size={24} color="#64748B" />
                        </TouchableOpacity>
                    )}

                    <View style={tw`flex-1 bg-gray-100 dark:bg-gray-800 rounded-3xl border border-transparent focus:border-brand-navy flex-row items-end px-2`}>
                        <TextInput
                            style={tw`flex-1 text-base px-3 py-3 text-gray-800 dark:text-white max-h-32`}
                            value={inputText}
                            onChangeText={setInputText}
                            placeholder="Mensagem"
                            placeholderTextColor="#94A3B8"
                            multiline={true}
                            onKeyPress={handleKeyPress}
                        />
                        {!inputText && !loading && (
                            <TouchableOpacity style={tw`p-2`}>
                                <MaterialIcons name="sticky-note-2" size={22} color="#94A3B8" />
                            </TouchableOpacity>
                        )}
                    </View>

                    <TouchableOpacity
                        style={tw.style(
                            `p-3 rounded-full shadow-sm items-center justify-center w-12 h-12`,
                            (inputText || loading) ? 'bg-blue-900' : 'bg-gray-200 dark:bg-gray-800'
                        )}
                        onPress={loading ? handleStop : (inputText ? handleSend : null)}
                    >
                        {loading ? (
                            <MaterialIcons name="stop" size={24} color="white" />
                        ) : inputText ? (
                            <MaterialIcons name="send" size={24} color="white" />
                        ) : (
                            <MaterialIcons name="mic" size={24} color="#64748B" />
                        )}
                    </TouchableOpacity>
                </View>
            </View>
        </KeyboardAvoidingView>
    );
}
