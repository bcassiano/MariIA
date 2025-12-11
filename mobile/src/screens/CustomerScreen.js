import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, Alert } from 'react-native';
import { getCustomer, generatePitch } from '../services/api';

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
        <ScrollView style={styles.container}>
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
