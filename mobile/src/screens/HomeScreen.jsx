// Force update
import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Platform, ScrollView, Image, Modal } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getInsights, getInactiveCustomers, getBalesBreakdown } from '../services/api';
import { create } from 'twrnc';
import Svg, { Rect, Path, G } from 'react-native-svg';
import Icon from '../components/Icon';

import { AuthService } from '../services/auth';
import { SapService } from '../services/sapService';

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
    const [userStatus, setUserStatus] = useState('checking'); // 'checking' | 'active' | 'pending'

    const filters = [
        { label: '15-25', min: 15, max: 25 },
        { label: '26-30', min: 26, max: 30 },
        { label: '30', val: 30 },
        { label: '60', val: 60 },
        { label: '90', val: 90 }
    ];

    useEffect(() => {
        checkUserStatus(true); // true = initial check (silent/local)
    }, []);

    useEffect(() => {
        if (userStatus === 'active') {
            loadData(selectedFilter, viewMode);
        }
    }, [selectedFilter, viewMode, userStatus]);

    const checkUserStatus = async (isInitial = false) => {
        try {
            if (!isInitial) setLoading(true);

            // 1. Try Local Storage first (fastest)
            const localStatus = await AsyncStorage.getItem('user_status');
            if (isInitial && localStatus) {
                console.log("HomeScreen: Initial local status:", localStatus);
                setUserStatus(localStatus);
                if (localStatus === 'pending') setLoading(false);
                return;
            }

            // 2. If manual check or no local status, verify with Server
            const user = AuthService.getCurrentUser();
            if (!user) {
                console.warn("HomeScreen: No auth user found during check.");
                setUserStatus('pending'); // Safety net
                setLoading(false);
                return;
            }

            // 🔐 ADMIN BYPASS: Always Active for Admin
            if (user.email === 'bruno.cassiano@fantasticoalimentos.com.br') {
                console.log("🔐 HomeScreen: Admin Bypass for Renata active.");
                await AsyncStorage.setItem('user_status', 'active');
                setUserStatus('active');
                setLoading(false);
                return;
            }

            let slpCode = null;
            try {
                // Race condition: Firestore fetch vs 3s timeout (Same logic as App.js)
                const firestorePromise = AuthService.getSapId(user.uid);
                const timeoutPromise = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error("Firestore timeout")), 3000)
                );

                slpCode = await Promise.race([firestorePromise, timeoutPromise]);
            } catch (firestoreErr) {
                console.warn("HomeScreen: Firestore unavailable/slow. Using SapService fallback.");
                slpCode = await SapService.getSlpCodeByEmail(user.email);
            }

            // Retry logic if first attempt failed/returned null
            if (!slpCode) {
                slpCode = await SapService.getSlpCodeByEmail(user.email);
            }

            if (slpCode) {
                console.log("HomeScreen: User Activated! SAP ID:", slpCode);
                await AsyncStorage.setItem('user_session_id', slpCode.toString());
                await AsyncStorage.setItem('auth_strategy', 'firebase');
                await AsyncStorage.setItem('user_status', 'active');
                setUserStatus('active');
                // Effect will trigger loadData
            } else {
                console.log("HomeScreen: User still pending.");
                await AsyncStorage.setItem('user_status', 'pending');
                setUserStatus('pending');
                alert("Seu cadastro ainda está em análise. Por favor, aguarde a ativação.");
            }
        } catch (e) {
            console.error("Error checking user status:", e);

            // Check if it's a specific "User not found" error from SapService
            if (e.message && e.message.includes("não foi encontrado")) {
                await AsyncStorage.setItem('user_status', 'pending');
                setUserStatus('pending');
                if (!isInitial) alert("Seu cadastro ainda não foi ativado no SAP. Por favor, aguarde.");
                return;
            }

            // Don't block active users on error, but block pending ones
            const currentStatus = await AsyncStorage.getItem('user_status');
            if (currentStatus === 'active') {
                setUserStatus('active');
            } else {
                setUserStatus('pending');
                if (!isInitial) alert("Erro ao verificar status. Verifique sua conexão.");
            }
        } finally {
            setLoading(false);
        }
    };

    const loadData = async (filter, mode) => {
        // Prevent loading if not active
        if (userStatus !== 'active') return;

        setLoading(true);
        setErrorMsg(null);
        try {
            let minDays, maxDays;

            if (filter.min !== undefined) {
                // Range específico (Ex: 15-25 dias)
                minDays = filter.min;
                maxDays = filter.max;
            } else {
                // Padrão (30/60/90 dias)
                if (mode === 'active') {
                    // Positivados: últimos X dias (range inclusivo de 0 até X)
                    // Ex: "30 dias" = clientes que compraram nos últimos 0-30 dias
                    minDays = 0;
                    maxDays = filter.val;
                } else {
                    // Em Recuperação: X dias ou mais (range acumulativo)
                    // Ex: "30 dias" = clientes sem compras há 30+ dias
                    // Isso garante que sempre haverá resultados se existirem inativos
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
            setSelectedCustomerName(`${item.Codigo_Cliente} - ${item.Nome_Cliente}`);
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
                        <Icon
                            name="chevron_right"
                            size={18}
                            color={viewMode === 'active' ? '#1A2F5A' : '#EF4444'}
                        />
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
                                style={tw`items-end bg-blue-50 px-2 py-1 rounded-lg border border-blue-100`}
                                onPress={() => handleMediaFDPress(item)}
                            >
                                <Text style={tw`text-[10px] uppercase tracking-wider text-blue-600 mb-0.5 font-bold`}>
                                    Média FD:
                                </Text>
                                <Text style={tw`text-sm font-bold text-blue-900`}>
                                    {typeof item.Media_Fardos === 'number' ? item.Media_Fardos.toFixed(1) : item.Media_Fardos}
                                </Text>
                            </TouchableOpacity>
                        )}
                    </View>
                </View>
            </View>
        </TouchableOpacity>
    );

    if (loading || userStatus === 'checking') {
        return (
            <View style={tw`flex-1 justify-center items-center bg-gray-50`}>
                <ActivityIndicator size="large" color="#1A2F5A" />
                <Text style={tw`text-gray-500 mt-4 font-medium`}>
                    {userStatus === 'checking' ? 'Validando acesso...' : 'Carregando insights...'}
                </Text>
            </View>
        );
    }

    // PENDING ACTIVATION STATE
    if (userStatus === 'pending') {
        return (
            <View style={tw`flex-1 bg-gray-50 px-6 justify-center items-center`}>
                <View style={tw`bg-white p-8 rounded-2xl shadow-lg w-full items-center`}>
                    <View style={tw`bg-yellow-100 p-4 rounded-full mb-4`}>
                        <Icon name="timer" size={48} color="#f59e0b" />
                    </View>
                    <Text style={tw`text-2xl font-bold text-gray-800 text-center mb-2`}>
                        Cadastro em Análise
                    </Text>
                    <Text style={tw`text-gray-600 text-center mb-6 leading-6`}>
                        Olá! Seu usuário foi criado, mas ainda não está vinculado a uma equipe de vendas no SAP.
                    </Text>
                    <View style={tw`bg-blue-50 p-4 rounded-xl mb-6 w-full`}>
                        <Text style={tw`text-blue-800 text-center font-medium`}>
                            Solicite a ativação ao TI ou ao seu Gerente Comercial.
                        </Text>
                    </View>
                    <TouchableOpacity
                        style={tw`bg-[#1A2F5A] py-3.5 px-8 rounded-full mb-4 shadow-md flex-row items-center gap-2`}
                        onPress={() => checkUserStatus(false)}
                    >
                        <Icon name="refresh" size={20} color="#FFF" />
                        <Text style={tw`text-white font-bold text-base`}>Verificar Novamente</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        onPress={() => AuthService.logout()}
                        style={tw`flex-row items-center justify-center py-2 px-4 rounded-full border border-gray-100 bg-white shadow-sm`}
                    >
                        <Icon name="logout" size={18} color="#EF4444" />
                        <Text style={tw`text-gray-600 font-medium ml-2`}>Sair</Text>
                    </TouchableOpacity>

                </View>
            </View>
        );
    }

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

                {/* Botão Minha Carteira */}
                <TouchableOpacity
                    style={[tw`rounded-2xl p-4 mb-6 shadow-lg flex-row items-center justify-between`, { backgroundColor: '#1A2F5A' }]}
                    onPress={() => navigation.navigate('Portfolio')}
                    activeOpacity={0.8}
                >
                    <View style={tw`flex-row items-center gap-3`}>
                        <View style={[tw`w-12 h-12 rounded-full items-center justify-center`, { backgroundColor: '#0F1F3D' }]}>
                            <Icon name="donut_large" size={28} color="#FFF" />
                        </View>
                        <View>
                            <Text style={tw`text-white font-bold text-lg`}>📊 Minha Carteira</Text>
                            <Text style={tw`text-blue-100 text-sm font-semibold`}>Análise de positivação</Text>
                        </View>
                    </View>
                    <Icon name="chevron_right" size={28} color="#FFF" />
                </TouchableOpacity>

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
                    ListFooterComponent={
                        <View style={tw`py-4 px-6 items-center`}>
                            <Text style={tw`text-[10px] text-gray-400 text-center leading-tight`}>
                                A Mari IA pode cometer erros. As informações devem ser verificadas.
                            </Text>
                        </View>
                    }
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
                                <Icon name="close" size={24} color="#64748B" />
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
                                        <Icon name="inventory_2" size={48} color="#E2E8F0" />
                                        <Text style={tw`text-gray-400 mt-4 font-medium`}>Nenhum histórico detalhado nos últimos 180 dias.</Text>
                                    </View>
                                )}
                                showsVerticalScrollIndicator={false}
                            />
                        )}

                        <View style={tw`mt-4 p-4 bg-gray-50 rounded-2xl flex-row items-center gap-3`}>
                            <Icon name="info" size={20} color="#64748B" />
                            <Text style={tw`text-[11px] text-gray-500 flex-1 leading-snug`}>
                                Estes valores representam a média de fardos por SKU considerando os pedidos dos últimos 6 meses.
                            </Text>
                        </View>
                    </View>
                </View>
            </Modal>

            {/* Floating Chat Button */}
            <TouchableOpacity
                style={tw`absolute bottom-8 right-8 bg-accent-btn w-16 h-16 rounded-full items-center justify-center shadow-lg z-50`}
                onPress={() => navigation.navigate('Chat')}
                activeOpacity={0.8}
            >
                <Icon name="chat_bubble" size={28} color="white" />
            </TouchableOpacity>
        </View>
    );
}
