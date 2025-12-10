import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, Alert } from 'react-native';
import { getCustomer, generatePitch } from '../services/api';

export default function CustomerScreen({ route }) {
    const { cardCode } = route.params;
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [pitchLoading, setPitchLoading] = useState(false);
    const [pitch, setPitch] = useState(null);

    useEffect(() => {
        loadCustomerData();
    }, []);

    const loadCustomerData = async () => {
        setLoading(true);
        const result = await getCustomer(cardCode);
        if (result && result.history) {
            setHistory(result.history);
        }
        setLoading(false);
    };

    const handleGeneratePitch = async () => {
        setPitchLoading(true);
        setPitch(null);
        const result = await generatePitch(cardCode, ""); // SKU opcional
        if (result && result.pitch) {
            setPitch(result.pitch);
        } else {
            Alert.alert("Erro", "Não foi possível gerar o pitch.");
        }
        setPitchLoading(false);
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };

    const renderHistoryItem = ({ item }) => (
        <View style={styles.historyItem}>
            <View style={styles.row}>
                <Text style={styles.date}>{item.Data_Emissao}</Text>
                <Text style={styles.status}>{item.Status_Documento}</Text>
            </View>
            <Text style={styles.product}>{item.Nome_Produto}</Text>
            <View style={styles.row}>
                <Text>Qtd: {item.Quantidade}</Text>
                <Text style={styles.value}>{formatCurrency(item.Valor_Liquido)}</Text>
            </View>
        </View>
    );

    return (
        <ScrollView style={styles.container}>
            <View style={styles.headerContainer}>
                <Text style={styles.title}>{cardCode}</Text>
                <TouchableOpacity
                    style={styles.pitchButton}
                    onPress={handleGeneratePitch}
                    disabled={pitchLoading}
                >
                    {pitchLoading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.pitchButtonText}>✨ Gerar Pitch IA</Text>
                    )}
                </TouchableOpacity>
            </View>

            {pitch && (
                <View style={styles.pitchContainer}>
                    <Text style={styles.pitchTitle}>Sugestão da MariIA:</Text>
                    <Text style={styles.pitchText}>{pitch}</Text>
                </View>
            )}

            <Text style={styles.sectionTitle}>Histórico Recente</Text>
            {loading ? (
                <ActivityIndicator size="large" color="#0000ff" />
            ) : (
                <FlatList
                    data={history}
                    keyExtractor={(item, index) => index.toString()}
                    renderItem={renderHistoryItem}
                    scrollEnabled={false} // Scroll controlado pelo ScrollView pai
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
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 10,
        marginTop: 10,
    },
    historyItem: {
        backgroundColor: 'white',
        padding: 12,
        borderRadius: 8,
        marginBottom: 8,
        elevation: 1,
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
    status: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#444',
    },
    product: {
        fontSize: 14,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    value: {
        color: '#008000',
        fontWeight: 'bold',
    },
});
