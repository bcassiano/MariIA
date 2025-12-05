import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { sendChatMessage } from '../services/api';

export default function ChatScreen() {
    const [messages, setMessages] = useState([
        { id: 1, text: "Olá! Sou a MariIA. Como posso ajudar nas suas vendas hoje?", sender: 'bot' }
    ]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const flatListRef = useRef(null);

    const handleSend = async () => {
        if (!inputText.trim()) return;

        const userMsg = { id: Date.now(), text: inputText, sender: 'user' };
        setMessages(prev => [...prev, userMsg]);
        setInputText('');
        setLoading(true);

        try {
            const result = await sendChatMessage(userMsg.text);
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

    useEffect(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
    }, [messages]);

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
