// Force update
import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Platform, ScrollView, Image } from 'react-native';
import { getInsights, getInactiveCustomers } from '../services/api';
import { create } from 'twrnc';

// Load Tailwind config
const tw = create(require('../../tailwind.config.js'));

export default function HomeScreen({ navigation }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [errorMsg, setErrorMsg] = useState(null);
    // Filtro inicial: 30 dias
    const [selectedFilter, setSelectedFilter] = useState({ label: '30', val: 30 });
    const [viewMode, setViewMode] = useState('active'); // 'active' | 'inactive'

    const filters = [
        { label: '15-25', min: 15, max: 25 },
        { label: '26-30', min: 26, max: 30 },
        { label: '30', val: 30 },
        { label: '60', val: 60 },
        { label: '90', val: 90 }
    ];

    useEffect(() => {
        loadData(selectedFilter, viewMode);
    }, [selectedFilter, viewMode]);

    const loadData = async (filter, mode) => {
        setLoading(true);
        setErrorMsg(null);
        try {
            let minDays, maxDays;

            if (filter.min !== undefined) {
                // Range específico (Ex: 15-25)
                minDays = filter.min;
                maxDays = filter.max;
            } else {
                // Padrão (30/60/90)
                if (mode === 'active') {
                    minDays = 0;
                    maxDays = filter.val;
                } else {
                    minDays = filter.val;
                    maxDays = 9999;
                }
            }

            let result;
            if (mode === 'active') {
                result = await getInsights(minDays, maxDays);
            } else {
                result = await getInactiveCustomers(minDays, maxDays);
            }

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

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR');
    };

    const renderItem = ({ item }) => (
        <TouchableOpacity
            style={tw.style(
                `bg-white dark:bg-card-dark rounded-3xl mb-4 shadow-sm border border-gray-100 dark:border-gray-800 flex-row overflow-hidden`,
                // viewMode === 'inactive' && 'border-l-[8px] border-l-accent' // Removed problematic border
            )}
            onPress={() => navigation.navigate('Customer', { cardCode: item.Codigo_Cliente })}
        >
            {/* Left color strip - now a dedicated View column */}
            {/* Left color strip - self-stretch by default in flex-row */}
            {viewMode === 'inactive' && (
                <View style={tw`w-2 bg-accent rounded-tl-3xl rounded-bl-3xl`}></View>
            )}

            <View style={tw`flex-1 p-5 pl-4`}>
                <View style={tw`flex-row justify-between items-start mb-2`}>
                    <Text style={tw`text-[11px] font-bold text-primary bg-blue-50 px-3 py-1 rounded-full uppercase tracking-wider`}>
                        {item.Codigo_Cliente}
                    </Text>
                </View>

                <Text style={tw`text-[15px] font-bold text-primary mb-1.5 leading-snug`} numberOfLines={1}>
                    {item.Nome_Cliente}
                </Text>

                <View style={tw`flex-row items-center mb-4`}>
                    <Text style={tw`text-xs text-text-sub-light font-medium`}>
                        {item.Cidade} - {item.Estado}
                    </Text>
                </View>

                <View style={tw`border-t border-gray-100 pt-3 flex-row items-end justify-between`}>
                    <View>
                        <Text style={tw`text-[10px] uppercase tracking-wider text-text-sub-light mb-0.5 font-medium`}>
                            {viewMode === 'active' ? 'Total Vendas' : 'Sem compra desde'}
                        </Text>
                        <Text style={tw.style(
                            `text-sm font-bold`,
                            viewMode === 'active' ? 'text-green-600' : 'text-accent'
                        )}>
                            {viewMode === 'active' ? formatCurrency(item.Total_Venda) : formatDate(item.Ultima_Compra)}
                        </Text>
                    </View>

                    <View style={tw`flex-row items-center`}>
                        {item.Media_Fardos != null && (
                            <View style={tw`items-end mr-3`}>
                                <Text style={tw`text-[10px] uppercase tracking-wider text-text-sub-light mb-0.5 font-medium`}>
                                    Média FD:
                                </Text>
                                <Text style={tw`text-sm font-bold text-green-600`}>
                                    {item.Media_Fardos}
                                </Text>
                            </View>
                        )}

                        <View style={tw.style(
                            `w-8 h-8 rounded-full flex items-center justify-center`,
                            viewMode === 'active' ? 'bg-primary/10' : 'bg-red-50'
                        )}>
                            <Text style={tw.style(
                                `font-bold`,
                                viewMode === 'active' ? 'text-primary' : 'text-accent'
                            )}>
                                {'>'}
                            </Text>
                        </View>
                    </View>
                </View>
            </View>
        </TouchableOpacity>
    );

    return (
        <View style={tw`flex-1 bg-background-light p-4`}>
            {/* Header Section */}
            <View style={tw`mt-10 mb-6`}>
                <View style={tw`flex-row items-center gap-4 mb-5`}>
                    <View style={tw`w-16 h-16 rounded-full bg-white items-center justify-center shadow-sm border border-gray-100`}>
                        <Image
                            source={require('../../assets/logo_fantastico.png')}
                            style={tw`w-12 h-12`}
                            resizeMode="contain"
                        />
                    </View>
                    <View>
                        <Text style={tw`text-xl font-bold text-primary leading-tight`}>Performance de Clientes</Text>
                        <Text style={tw`text-xs text-text-sub-light`}>Análise de vendas e recuperação</Text>
                    </View>
                </View>

                {/* Toggle Buttons */}
                <View style={tw`flex-row bg-white p-1.5 rounded-2xl shadow-sm border border-gray-100 mb-6`}>
                    <TouchableOpacity
                        style={tw.style(
                            `flex-1 py-3 rounded-xl items-center justify-center flex-row gap-2`,
                            viewMode === 'active' ? 'bg-primary' : 'bg-transparent'
                        )}
                        onPress={() => setViewMode('active')}
                    >
                        <Text style={tw.style(
                            `text-sm font-bold`,
                            viewMode === 'active' ? 'text-white' : 'text-text-sub-light'
                        )}>
                            {viewMode === 'active' ? '✓ ' : ''}Positivados
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={tw.style(
                            `flex-1 py-3 rounded-xl items-center justify-center flex-row gap-2`,
                            viewMode === 'inactive' ? 'bg-primary' : 'bg-transparent'
                        )}
                        onPress={() => setViewMode('inactive')}
                    >
                        <Text style={tw.style(
                            `text-sm font-bold`,
                            viewMode === 'inactive' ? 'text-white' : 'text-text-sub-light'
                        )}>
                            ↺ Em Recuperação
                        </Text>
                    </TouchableOpacity>
                </View>

                {/* Filters ScrollView */}
                <View>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10, paddingBottom: 5 }}>
                        {filters.map((f) => (
                            <TouchableOpacity
                                key={f.label}
                                style={tw.style(
                                    `px-5 py-2 rounded-2xl border shadow-sm`,
                                    selectedFilter.label === f.label ? 'bg-accent-btn border-accent-btn' : 'bg-white border-gray-200'
                                )}
                                onPress={() => setSelectedFilter(f)}
                            >
                                <Text style={tw.style(
                                    `text-xs font-semibold`,
                                    selectedFilter.label === f.label ? 'text-white' : 'text-text-sub-light'
                                )}>
                                    {f.label} dias
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>
                </View>
            </View>

            {errorMsg && (
                <View style={tw`p-4 bg-red-50 mb-4 rounded-lg border border-red-200`}>
                    <Text style={tw`text-red-700 mb-2`}>Erro: {errorMsg}</Text>
                    <TouchableOpacity onPress={() => loadData(selectedFilter, viewMode)} style={tw`bg-red-700 p-2 rounded items-center`}>
                        <Text style={tw`text-white font-bold`}>Tentar Novamente</Text>
                    </TouchableOpacity>
                </View>
            )}

            {loading ? (
                <ActivityIndicator size="large" color="#1A2F5A" />
            ) : (
                <FlatList
                    data={data}
                    keyExtractor={(item, index) => index.toString()}
                    renderItem={renderItem}
                    refreshing={loading}
                    onRefresh={() => loadData(selectedFilter, viewMode)}
                    ListEmptyComponent={!loading && !errorMsg && <Text style={tw`text-center text-gray-500 mt-10`}>Nenhum dado encontrado.</Text>}
                    style={{ flex: 1 }}
                    contentContainerStyle={{ paddingBottom: 100 }}
                    showsVerticalScrollIndicator={false}
                />
            )}

            <TouchableOpacity
                style={tw`absolute bottom-6 right-6 bg-accent-btn w-16 h-16 rounded-full items-center justify-center shadow-lg elevation-5 z-50 border-2 border-white`}
                onPress={() => navigation.navigate('Chat')}
            >
                <Text style={tw`text-3xl text-white`}>💬</Text>
            </TouchableOpacity>
        </View>
    );
}
