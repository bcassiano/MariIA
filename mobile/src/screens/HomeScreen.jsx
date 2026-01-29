// Force update
import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Platform, ScrollView, Image, Modal } from 'react-native';
import { getInsights, getInactiveCustomers, getBalesBreakdown } from '../services/api';
import { create } from 'twrnc';
import { MaterialIcons } from '@expo/vector-icons';
import Svg, { Rect, Path, G } from 'react-native-svg';

// Load Tailwind config
const tw = create(require('../../tailwind.config.js'));

export default function HomeScreen({ navigation }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [errorMsg, setErrorMsg] = useState(null);

    // Analytical Breakdown State
    const [breakdownData, setBreakdownData] = useState([]);
    const [showBreakdownModal, setShowBreakdownModal] = useState(false);
    const [breakdownLoading, setBreakdownLoading] = useState(false);
    const [selectedCustomerName, setSelectedCustomerName] = useState('');
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

    const handleMediaFDPress = async (item) => {
        try {
            setSelectedCustomerName(item.Nome_Cliente);
            setBreakdownLoading(true);
            setShowBreakdownModal(true);
            const result = await getBalesBreakdown(item.Codigo_Cliente);
            setBreakdownData(result);
        } catch (err) {
            console.error("Error loading breakdown:", err);
        } finally {
            setBreakdownLoading(false);
        }
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
                `bg-white dark:bg-card-dark rounded-3xl mb-5 shadow-md border border-gray-100 dark:border-gray-800 flex-row overflow-hidden`,
            )}
            onPress={() => navigation.navigate('Customer', { cardCode: item.Codigo_Cliente })}
        >
            {/* Left color strip - now a dedicated View column */}
            {/* Left color strip - self-stretch by default in flex-row */}
            {viewMode === 'inactive' && (
                <View style={tw`w-2 bg-accent rounded-tl-3xl rounded-bl-3xl`}></View>
            )}

            <View style={tw`flex-1 p-5 pl-4`}>
                <View style={tw`flex-row justify-between items-center mb-2`}>
                    <Text style={tw`text-[11px] font-bold text-primary bg-blue-50 px-3 py-1 rounded-full uppercase tracking-wider`}>
                        {item.Codigo_Cliente}
                    </Text>
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
                            <TouchableOpacity
                                style={tw`items-end bg-green-50 px-2 py-1 rounded-lg border border-green-100`}
                                onPress={() => handleMediaFDPress(item)}
                            >
                                <Text style={tw`text-[10px] uppercase tracking-wider text-green-700 mb-0.5 font-bold`}>
                                    Média FD:
                                </Text>
                                <Text style={tw`text-sm font-bold text-green-600`}>
                                    {item.Media_Fardos}
                                </Text>
                            </TouchableOpacity>
                        )}
                    </View>
                </View>
            </View>
        </TouchableOpacity>
    );

    return (
        <View style={tw`flex-1 bg-background-light p-4`}>
            {/* Subtle Texture Pattern */}
            <View style={[tw`absolute inset-0`, { opacity: 0.05 }]}>
                <Svg width="100%" height="100%">
                    <Path
                        d="M0 0h100v100H0z"
                        fill="none"
                    />
                    <G fill="#1A2F5A">
                        {/* Simple subtle dot grid for texture */}
                        {Array.from({ length: 20 }).map((_, i) =>
                            Array.from({ length: 40 }).map((_, j) => (
                                <Rect key={`${i}-${j}`} x={i * 25} y={j * 25} width="1" height="1" rx="0.5" />
                            ))
                        )}
                    </G>
                </Svg>
            </View>
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
                <View style={tw`flex-row bg-white rounded-2xl shadow-sm border border-gray-100 mb-6`}>
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

            {/* Analytical Breakdown Modal */}
            <Modal
                visible={showBreakdownModal}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowBreakdownModal(false)}
            >
                <View style={tw`flex-1 justify-end bg-black/50`}>
                    <View style={tw`bg-white rounded-t-3xl p-6 h-2/3 shadow-xl`}>
                        <View style={tw`flex-row justify-between items-center mb-6`}>
                            <View style={tw`flex-1`}>
                                <Text style={tw`text-xs font-bold text-primary uppercase tracking-widest`}>Breakdown Analítico</Text>
                                <Text style={tw`text-lg font-bold text-indigo-900`} numberOfLines={1}>{selectedCustomerName}</Text>
                            </View>
                            <TouchableOpacity
                                onPress={() => {
                                    setShowBreakdownModal(false);
                                    setBreakdownData([]);
                                }}
                                style={tw`bg-gray-100 p-2 rounded-full`}
                            >
                                <MaterialIcons name="close" size={24} color="#64748B" />
                            </TouchableOpacity>
                        </View>

                        {breakdownLoading ? (
                            <View style={tw`flex-1 items-center justify-center`}>
                                <ActivityIndicator size="large" color="#1A2F5A" />
                                <Text style={tw`mt-4 text-gray-500 font-medium`}>Analisando SKUs...</Text>
                            </View>
                        ) : (
                            <FlatList
                                data={breakdownData}
                                keyExtractor={(item) => item.SKU}
                                renderItem={({ item }) => (
                                    <View style={tw`flex-row py-4 border-b border-gray-50 items-center`}>
                                        <View style={tw`flex-1 pr-4`}>
                                            <Text style={tw`text-sm font-bold text-gray-800 mb-0.5`}>{item.Produto}</Text>
                                            <Text style={tw`text-[10px] text-gray-400 font-medium`}>SKU: {item.SKU} • {item.Vezes_Comprado} pedidos</Text>
                                        </View>
                                        <View style={tw`items-end bg-blue-50 px-3 py-1.5 rounded-xl border border-blue-100`}>
                                            <Text style={tw`text-[9px] uppercase font-bold text-blue-600 mb-0.5`}>Média</Text>
                                            <Text style={tw`text-base font-bold text-blue-900`}>{item.Media_SKU}</Text>
                                        </View>
                                    </View>
                                )}
                                ListEmptyComponent={() => (
                                    <View style={tw`items-center justify-center mt-20`}>
                                        <MaterialIcons name="inventory_2" size={48} color="#E2E8F0" />
                                        <Text style={tw`text-gray-400 mt-4 font-medium`}>Nenhum histórico detalhado nos últimos 180 dias.</Text>
                                    </View>
                                )}
                                showsVerticalScrollIndicator={false}
                            />
                        )}

                        <View style={tw`mt-4 p-4 bg-gray-50 rounded-2xl flex-row items-center gap-3`}>
                            <MaterialIcons name="info" size={20} color="#64748B" />
                            <Text style={tw`text-[11px] text-gray-500 flex-1 leading-snug`}>
                                Estes valores representam a média de fardos por SKU considerando os pedidos dos últimos 6 meses.
                            </Text>
                        </View>
                    </View>
                </View>
            </Modal>
        </View>
    );
}
