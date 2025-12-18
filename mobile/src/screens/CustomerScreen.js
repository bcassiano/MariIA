import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, Alert } from 'react-native';
import { getCustomer, generatePitch, sendPitchFeedback } from '../services/api';

export default function CustomerScreen({ route }) {
    const { cardCode } = route.params;
    const [history, setHistory] = useState([]);
    const [customerName, setCustomerName] = useState('');
    const [loading, setLoading] = useState(true);
    const [pitchLoading, setPitchLoading] = useState(false);
    const [pitch, setPitch] = useState(null);

    useEffect(() => {
        loadCustomerData();
    }, []);

    const loadCustomerData = async () => {
        setLoading(true);
        const result = await getCustomer(cardCode);
        if (result) {
            if (result.history) setHistory(result.history);
            if (result.customer_name) setCustomerName(result.customer_name);
        }
        setLoading(false);
    };

    const [pitchId, setPitchId] = useState(null);
    const [feedbackGiven, setFeedbackGiven] = useState(false);

    const handleGeneratePitch = async () => {
        setPitchLoading(true);
        setPitch(null);
        setPitchId(null);
        setFeedbackGiven(false);
        const result = await generatePitch(cardCode, ""); // SKU opcional
        if (result && result.pitch) {
            setPitch(result.pitch);
            setPitchId(result.pitch_id);
        } else {
            Alert.alert("Erro", "Não foi possível gerar o pitch.");
        }
        setPitchLoading(false);
    };

    const handleFeedback = async (type) => {
        if (!pitchId) return;
        setFeedbackGiven(true);
        await sendPitchFeedback(pitchId, type);
        Alert.alert("Obrigado!", "Seu feedback ajuda a Mari IA a aprender.");
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    };

    const DocumentCard = ({ item }) => {
        const [expanded, setExpanded] = useState(false);

        return (
            <View style={styles.documentCard}>
                <TouchableOpacity
                    style={styles.documentHeader}
                    onPress={() => setExpanded(!expanded)}
                >
                    <View style={styles.row}>
                        <Text style={styles.date}>{formatDate(item.date)}</Text>
                        <Text style={styles.docNum}>{item.type || 'Doc'}: {item.document_number}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.status}>{item.status}</Text>
                        <Text style={styles.totalValue}>{formatCurrency(item.total_value)}</Text>
                    </View>
                    <Text style={styles.expandText}>{expanded ? "▲ Ocultar Itens" : "▼ Ver Itens"}</Text>
                </TouchableOpacity>

                {expanded && (
                    <View style={styles.itemsContainer}>
                        {item.items.map((prod, index) => (
                            <View key={index} style={styles.productItem}>
                                <Text style={styles.productName}>{prod.Nome_Produto}</Text>
                                <View style={styles.row}>
                                    <Text style={styles.productQty}>Qtd: {prod.Quantidade}</Text>
                                    <Text style={styles.productValue}>{formatCurrency(prod.Valor_Liquido)}</Text>
                                </View>
                            </View>
                        ))}
                    </View>
                )}
            </View>
        );
    };

    return (
        <ScrollView style={styles.container} contentContainerStyle={{ flexGrow: 1, paddingBottom: 20 }}>
            <View style={styles.headerContainer}>
                <Text style={styles.title}>{cardCode} - {customerName || 'Carregando...'}</Text>
                <TouchableOpacity
                    style={styles.pitchButton}
                    onPress={handleGeneratePitch}
                    disabled={pitchLoading}
                >
                    {pitchLoading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.pitchButtonText}>🪄✨ Gerar Pitch IA</Text>
                    )}
                </TouchableOpacity>
            </View>

            {pitch && (
                <View style={styles.pitchContainer}>
                    <Text style={styles.pitchTitle}>Sugestão da Mari IA:</Text>
                    <Text style={styles.pitchText}>{pitch}</Text>

                    {/* Botões de Feedback */}
                    {!feedbackGiven ? (
                        <View style={styles.feedbackContainer}>
                            <Text style={styles.feedbackLabel}>Isso ajudou?</Text>
                            <View style={styles.feedbackButtons}>
                                <TouchableOpacity
                                    style={[styles.feedbackBtn, styles.usefulBtn]}
                                    onPress={() => handleFeedback('useful')}
                                >
                                    <Text style={styles.feedbackText}>👍 Útil</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={[styles.feedbackBtn, styles.soldBtn]}
                                    onPress={() => handleFeedback('sold')}
                                >
                                    <Text style={styles.feedbackText}>💰 Vendi!</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    ) : (
                        <Text style={styles.thankYouText}>Obrigado pelo feedback! 🚀</Text>
                    )}
                </View>
            )}

            <Text style={styles.sectionTitle}>Histórico Recente</Text>
            {loading ? (
                <ActivityIndicator size="large" color="#0000ff" />
            ) : (
                <FlatList
                    data={history}
                    keyExtractor={(item) => item.document_number.toString()}
                    renderItem={({ item }) => <DocumentCard item={item} />}
                    scrollEnabled={false}
                    ListEmptyComponent={<Text>Nenhum histórico encontrado.</Text>}
                />
            )}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        padding: 15,
    },
    headerContainer: {
        marginBottom: 20,
    },
    title: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 10,
    },
    pitchButton: {
        backgroundColor: '#6200ee',
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        elevation: 3,
    },
    pitchButtonText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
    },
    pitchContainer: {
        backgroundColor: '#e8eaf6',
        padding: 15,
        borderRadius: 8,
        marginBottom: 20,
        borderLeftWidth: 4,
        borderLeftColor: '#6200ee',
    },
    pitchTitle: {
        fontWeight: 'bold',
        color: '#6200ee',
        marginBottom: 5,
    },
    pitchText: {
        color: '#333',
        lineHeight: 22,
    },
    feedbackContainer: {
        marginTop: 15,
        paddingTop: 15,
        borderTopWidth: 1,
        borderTopColor: '#ddd',
        alignItems: 'center',
    },
    feedbackLabel: {
        fontSize: 14,
        color: '#666',
        marginBottom: 10,
    },
    feedbackButtons: {
        flexDirection: 'row',
        gap: 15,
    },
    feedbackBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 8,
        paddingHorizontal: 16,
        borderRadius: 20,
        elevation: 1,
    },
    usefulBtn: {
        backgroundColor: '#e0e0e0',
    },
    soldBtn: {
        backgroundColor: '#4caf50',
    },
    feedbackText: {
        fontWeight: 'bold',
        color: '#333',
    },
    thankYouText: {
        marginTop: 15,
        textAlign: 'center',
        color: '#6200ee',
        fontWeight: 'bold',
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 10,
        marginTop: 10,
    },
    documentCard: {
        backgroundColor: 'white',
        borderRadius: 8,
        marginBottom: 10,
        elevation: 2,
        overflow: 'hidden',
    },
    documentHeader: {
        padding: 15,
        backgroundColor: '#fff',
    },
    itemsContainer: {
        backgroundColor: '#f9f9f9',
        padding: 10,
        borderTopWidth: 1,
        borderTopColor: '#eee',
    },
    productItem: {
        marginBottom: 8,
        paddingBottom: 8,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
    },
    productName: {
        fontSize: 14,
        color: '#333',
        marginBottom: 4,
    },
    productQty: {
        fontSize: 12,
        color: '#666',
    },
    productValue: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#008000',
    },
    row: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 4,
    },
    date: {
        color: '#666',
        fontSize: 12,
    },
    docNum: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#333',
    },
    status: {
        fontSize: 12,
        color: '#444',
    },
    totalValue: {
        color: '#008000',
        fontWeight: 'bold',
        fontSize: 14,
    },
    expandText: {
        fontSize: 10,
        color: '#6200ee',
        textAlign: 'center',
        marginTop: 5,
    }
});
