import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { getPortfolio } from '../services/api';
import DonutChart from '../components/DonutChart';
import { create } from 'twrnc';
import Icon from '../components/Icon';

const tw = create(require('../../tailwind.config.js'));

export default function PortfolioScreen({ navigation }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all'); // 'all', 'positivated', 'non_positivated'
    const [errorMsg, setErrorMsg] = useState(null);

    useEffect(() => {
        loadPortfolio();
    }, []);

    const loadPortfolio = async () => {
        setLoading(true);
        setErrorMsg(null);
        const result = await getPortfolio();

        if (result.error) {
            setErrorMsg(result.error);
        } else {
            setData(result);
        }
        setLoading(false);
    };

    const filteredClients = () => {
        if (!data || !data.clients) return [];
        if (filter === 'positivated') return data.clients.filter(c => c.is_positivated);
        if (filter === 'non_positivated') return data.clients.filter(c => !c.is_positivated);
        return data.clients;
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };

    if (loading) {
        return (
            <View style={tw`flex-1 items-center justify-center bg-background-light`}>
                <ActivityIndicator size="large" color="#1A2F5A" />
                <Text style={tw`mt-4 text-gray-500`}>Analisando carteira...</Text>
            </View>
        );
    }

    if (errorMsg) {
        return (
            <View style={tw`flex-1 bg-background-light p-4 justify-center`}>
                <View style={tw`bg-red-50 p-6 rounded-2xl border border-red-200`}>
                    <Text style={tw`text-red-700 text-center mb-4`}>Erro: {errorMsg}</Text>
                    <TouchableOpacity
                        onPress={loadPortfolio}
                        style={tw`bg-red-700 p-3 rounded-xl items-center`}
                    >
                        <Text style={tw`text-white font-bold`}>Tentar Novamente</Text>
                    </TouchableOpacity>
                </View>
            </View>
        );
    }

    if (!data || !data.summary) {
        return (
            <View style={tw`flex-1 bg-background-light items-center justify-center`}>
                <Text style={tw`text-gray-500`}>Nenhum dado disponível</Text>
            </View>
        );
    }

    return (
        <View style={tw`flex-1 bg-background-light`}>
            <ScrollView style={tw`flex-1`} contentContainerStyle={tw`p-4 pb-24`}>
                {/* Header */}
                <View style={tw`mt-10 mb-6 flex-row items-center`}>
                    <TouchableOpacity
                        onPress={() => navigation.goBack()}
                        style={tw`mr-4 w-10 h-10 rounded-full bg-white items-center justify-center shadow-sm`}
                    >
                        <Icon name="arrow_back" size={24} color="#1A2F5A" />
                    </TouchableOpacity>
                    <View style={tw`flex-1`}>
                        <Text style={tw`text-2xl font-bold text-primary mb-1`}>Minha Carteira</Text>
                        <Text style={tw`text-sm text-gray-600`}>Análise dos últimos 30 dias</Text>
                    </View>
                </View>

                {/* Gráfico */}
                <View style={tw`bg-white rounded-3xl p-6 mb-6 shadow-md`}>
                    <DonutChart
                        positivated={data.summary.positivated_clients}
                        nonPositivated={data.summary.non_positivated_clients}
                        rate={data.summary.positivation_rate}
                    />

                    <View style={tw`flex-row justify-around mt-6`}>
                        <View style={tw`items-center`}>
                            <View style={tw`flex-row items-center gap-2 mb-1`}>
                                <View style={tw`w-5 h-5 rounded-full bg-green-800`} />
                                <Text style={tw`text-xs text-gray-700 font-bold`}>Positivados</Text>
                            </View>
                            <Text style={tw`text-3xl font-bold text-green-800`}>
                                {data.summary.positivated_clients}
                            </Text>
                        </View>

                        <View style={tw`items-center`}>
                            <View style={tw`flex-row items-center gap-2 mb-1`}>
                                <View style={tw`w-5 h-5 rounded-full bg-red-800`} />
                                <Text style={tw`text-xs text-gray-700 font-bold`}>Sem Vendas</Text>
                            </View>
                            <Text style={tw`text-3xl font-bold text-red-800`}>
                                {data.summary.non_positivated_clients}
                            </Text>
                        </View>
                    </View>
                </View>

                {/* Filtros */}
                <View style={tw`flex-row gap-2 mb-4`}>
                    <TouchableOpacity
                        style={tw.style('flex-1 py-3 rounded-xl items-center',
                            filter === 'all' ? 'bg-primary' : 'bg-white border border-gray-200')}
                        onPress={() => setFilter('all')}
                    >
                        <Text style={tw.style('text-sm font-bold',
                            filter === 'all' ? 'text-white' : 'text-gray-600')}>
                            Todos ({data.summary.total_clients})
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={tw.style('flex-1 py-3 rounded-xl items-center',
                            filter === 'positivated' ? 'bg-green-800' : 'bg-white border border-gray-200')}
                        onPress={() => setFilter('positivated')}
                    >
                        <Text style={tw.style('text-sm font-bold',
                            filter === 'positivated' ? 'text-white' : 'text-gray-600')}>
                            ✓ {data.summary.positivated_clients}
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={tw.style('flex-1 py-3 rounded-xl items-center',
                            filter === 'non_positivated' ? 'bg-red-800' : 'bg-white border border-gray-200')}
                        onPress={() => setFilter('non_positivated')}
                    >
                        <Text style={tw.style('text-sm font-bold',
                            filter === 'non_positivated' ? 'text-white' : 'text-gray-600')}>
                            ✗ {data.summary.non_positivated_clients}
                        </Text>
                    </TouchableOpacity>
                </View>

                {/* Lista de Clientes */}
                {filteredClients().map((item) => (
                    <TouchableOpacity
                        key={item.card_code}
                        style={tw`bg-white rounded-2xl p-4 mb-3 shadow-sm flex-row items-center`}
                        onPress={() => navigation.navigate('Customer', { cardCode: item.card_code })}
                    >
                        <View style={tw.style('w-12 h-12 rounded-full items-center justify-center mr-3',
                            item.is_positivated ? 'bg-green-100' : 'bg-red-100')}>
                            <Icon
                                name={item.is_positivated ? 'check_circle' : 'cancel'}
                                size={28}
                                color={item.is_positivated ? '#15803D' : '#B91C1C'}
                            />
                        </View>

                        <View style={tw`flex-1`}>
                            <Text style={tw`text-sm font-bold text-primary mb-0.5`} numberOfLines={1}>
                                {item.name}
                            </Text>
                            <Text style={tw`text-xs text-gray-500`}>
                                {item.city} - {item.state} • {item.card_code}
                            </Text>
                            {item.is_positivated && (
                                <Text style={tw`text-xs text-green-800 font-bold mt-1`}>
                                    {formatCurrency(item.total_sales)}
                                </Text>
                            )}
                        </View>

                        <Icon name="chevron_right" size={20} color="#CBD5E1" />
                    </TouchableOpacity>
                ))}

                {filteredClients().length === 0 && (
                    <View style={tw`items-center py-10`}>
                        <Icon name="inbox" size={48} color="#E2E8F0" />
                        <Text style={tw`text-gray-500 mt-4`}>
                            Nenhum cliente nesta categoria
                        </Text>
                    </View>
                )}
            </ScrollView>
        </View>
    );
}
