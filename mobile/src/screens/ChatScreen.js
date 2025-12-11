import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sendChatMessage } from '../services/api';

const STORAGE_KEY = '@mariia_chat_history';

export default function ChatScreen({ navigation }) {
    const [messages, setMessages] = useState([
        { id: 1, text: "Olá! Sou a Mari IA. Como posso ajudar nas suas vendas hoje?", sender: 'bot' }
    ]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const flatListRef = useRef(null);

    // Carrega histórico ao iniciar
    useEffect(() => {
        loadHistory();
    }, []);

    // Salva histórico sempre que mudar (exceto se estiver vazio/inicial)
    useEffect(() => {
        if (messages.length > 1) {
            saveHistory();
        }
    }, [messages]);

    // Configura botão de Nova Conversa no Header
    useEffect(() => {
        navigation.setOptions({
            headerRight: () => (
                <TouchableOpacity onPress={confirmNewChat} style={styles.newChatButton}>
                    <Text style={styles.newChatButtonText}>✎ Nova Conversa</Text>
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
        Alert.alert(
            "Nova Conversa",
            "Deseja apagar o histórico e iniciar uma nova conversa?",
            [
                { text: "Cancelar", style: "cancel" },
                { text: "Sim, limpar", onPress: startNewChat, style: 'destructive' }
            ]
        );
    };

    const startNewChat = async () => {
        const initialMsg = [{ id: Date.now(), text: "Olá! Sou a Mari IA. Como posso ajudar nas suas vendas hoje?", sender: 'bot' }];
        setMessages(initialMsg);
        try {
            await AsyncStorage.removeItem(STORAGE_KEY);
        } catch (e) {
            console.error("Erro ao limpar histórico", e);
        }
    };

    const handleSend = async () => {
        if (!inputText.trim()) return;

        const userMsg = { id: Date.now(), text: inputText, sender: 'user' };
        setMessages(prev => [...prev, userMsg]);
        setInputText('');
        setLoading(true);

        try {
            const result = await sendChatMessage(userMsg.text, messages);
            const botMsg = {
                id: Date.now() + 1,
                text: result.response || "Desculpe, não entendi.",
                sender: 'bot'
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            const errorMsg = { id: Date.now() + 1, text: "Erro de conexão.", sender: 'bot' };
            setMessages(prev => [...prev, errorMsg]);
        }
        setLoading(false);
    };

    const renderItem = ({ item }) => (
        <View style={[
            styles.messageBubble,
            item.sender === 'user' ? styles.userBubble : styles.botBubble
        ]}>
            <Text style={[
                styles.messageText,
                item.sender === 'user' ? styles.userText : styles.botText
            ]}>{item.text}</Text>
        </View>
    );

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            keyboardVerticalOffset={80}
        >
            <FlatList
                ref={flatListRef}
                data={messages}
                keyExtractor={item => item.id.toString()}
                renderItem={renderItem}
                contentContainerStyle={styles.listContent}
                style={{ flex: 1 }}
                onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
            />

            <View style={styles.inputContainer}>
                <TextInput
                    style={styles.input}
                    value={inputText}
                    onChangeText={setInputText}
                    placeholder="Digite sua mensagem..."
                    placeholderTextColor="#999"
                />
                <TouchableOpacity
                    style={styles.sendButton}
                    onPress={handleSend}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.sendButtonText}>Enviar</Text>
                    )}
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        ...Platform.select({
            web: {
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
            }
        })
    },
    newChatButton: {
        marginRight: 15,
        backgroundColor: 'white',
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 20,
        elevation: 2,
    },
    newChatButtonText: {
        color: '#6200ee',
        fontWeight: 'bold',
        fontSize: 12,
    },
    listContent: {
        padding: 15,
        paddingBottom: 20,
    },
    messageBubble: {
        maxWidth: '80%',
        padding: 12,
        borderRadius: 15,
        marginBottom: 10,
    },
    userBubble: {
        alignSelf: 'flex-end',
        backgroundColor: '#6200ee',
        borderBottomRightRadius: 2,
    },
    botBubble: {
        alignSelf: 'flex-start',
        backgroundColor: 'white',
        borderBottomLeftRadius: 2,
        elevation: 1,
        ...Platform.select({
            web: {
                boxShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)',
            }
        })
    },
    messageText: {
        fontSize: 16,
    },
    userText: {
        color: 'white',
    },
    botText: {
        color: '#333',
    },
    inputContainer: {
        flexDirection: 'row',
        padding: 10,
        backgroundColor: 'white',
        elevation: 5,
        borderTopWidth: 1,
        borderTopColor: '#eee',
    },
    input: {
        flex: 1,
        backgroundColor: '#f0f0f0',
        borderRadius: 20,
        paddingHorizontal: 15,
        paddingVertical: 10,
        marginRight: 10,
        fontSize: 16,
    },
    sendButton: {
        backgroundColor: '#6200ee',
        borderRadius: 20,
        paddingHorizontal: 20,
        justifyContent: 'center',
        alignItems: 'center',
    },
    sendButtonText: {
        color: 'white',
        fontWeight: 'bold',
    },
});
