import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
import { getInsights } from '../services/api';

export default function HomeScreen({ navigation }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [errorMsg, setErrorMsg] = useState(null);
    const [days, setDays] = useState(30);

    useEffect(() => {
        loadData(days);
    }, [days]);

    const loadData = async (selectedDays) => {
        setLoading(true);
        setErrorMsg(null);
        try {
            const result = await getInsights(selectedDays);
            if (result.error) {
                setErrorMsg(result.error);
            } else {
                setData(result.data || []);
            }
        } catch (e) {
            setErrorMsg("Erro inesperado: " + e.message);
        }
        setLoading(false);
    };

    const renderItem = ({ item }) => (
        <TouchableOpacity
            style={styles.card}
            onPress={() => navigation.navigate('Customer', { cardCode: item.Nome_Cliente })}
        >
            <Text style={styles.customerName}>{item.Nome_Cliente}</Text>
            <View style={styles.row}>
                <Text style={styles.city}>{item.Cidade} - {item.Estado}</Text>
                <Text style={styles.value}>R$ {item.Total_Venda?.toFixed(2)}</Text>
            </View>
        </TouchableOpacity>
    );

    return (
        <View style={styles.container}>
            <View style={styles.headerContainer}>
                <Text style={styles.header}>Top Vendas</Text>
                <View style={styles.filterContainer}>
                    {[30, 60, 90].map((d) => (
                        <TouchableOpacity
                            key={d}
                            style={[styles.filterButton, days === d && styles.filterButtonActive]}
                            onPress={() => setDays(d)}
                        >
                            <Text style={[styles.filterText, days === d && styles.filterTextActive]}>{d} dias</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>

            {errorMsg && (
                <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>Erro: {errorMsg}</Text>
                    <TouchableOpacity onPress={() => loadData(days)} style={styles.retryButton}>
                        <Text style={styles.retryText}>Tentar Novamente</Text>
                    </TouchableOpacity>
                </View>
            )}

            {loading ? (
                <ActivityIndicator size="large" color="#0000ff" />
            ) : (
                <FlatList
                    data={data}
                    keyExtractor={(item, index) => index.toString()}
                    renderItem={renderItem}
                    refreshing={loading}
                    onRefresh={() => loadData(days)}
                    ListEmptyComponent={!loading && !errorMsg && <Text>Nenhum dado encontrado.</Text>}
                    style={{ flex: 1 }}
                    contentContainerStyle={{ paddingBottom: 100 }}
                />
            )}

            <TouchableOpacity
                style={styles.chatFab}
                onPress={() => navigation.navigate('Chat')}
            >
                <Text style={styles.chatFabText}>💬</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        padding: 10,
        ...Platform.select({
            web: {
                height: '100vh',
                overflow: 'hidden',
            }
        })
    },
    headerContainer: {
        marginTop: 40,
        marginBottom: 20,
    },
    header: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 10,
    },
    filterContainer: {
        flexDirection: 'row',
        gap: 10,
    },
    filterButton: {
        paddingVertical: 6,
        paddingHorizontal: 12,
        borderRadius: 20,
        backgroundColor: '#e0e0e0',
    },
    filterButtonActive: {
        backgroundColor: '#6200ee',
    },
    filterText: {
        color: '#333',
        fontWeight: '600',
    },
    filterTextActive: {
        color: 'white',
    },
    card: {
        backgroundColor: 'white',
        padding: 15,
        borderRadius: 10,
        marginBottom: 10,
        elevation: 2,
    },
    customerName: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 5,
    },
    row: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    city: {
        color: '#666',
    },
    value: {
        color: '#008000',
        fontWeight: 'bold',
    },
    errorContainer: {
        padding: 15,
        backgroundColor: '#ffebee',
        marginBottom: 15,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#ffcdd2'
    },
    errorText: {
        color: '#c62828',
        marginBottom: 10,
    },
    retryButton: {
        backgroundColor: '#c62828',
        padding: 10,
        borderRadius: 5,
        alignItems: 'center'
    },
    retryText: {
        color: 'white',
        fontWeight: 'bold'
    },
    chatFab: {
        position: 'absolute',
        bottom: 20,
        right: 20,
        backgroundColor: '#6200ee',
        width: 60,
        height: 60,
        borderRadius: 30,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        zIndex: 100,
    },
    chatFabText: {
        fontSize: 30,
    }
});
