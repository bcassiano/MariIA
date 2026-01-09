import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator, Image, SafeAreaView, Platform, Linking, Modal, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useNavigation } from '@react-navigation/native';
import { getCustomer, generatePitch, sendPitchFeedback, getCustomerTrends } from '../services/api';
import { create } from 'twrnc';
import Icon from '../components/Icon';

// Tailwind Config
const tw = create(require('../../tailwind.config.js'));

export default function CustomerScreen({ route }) {
    const { cardCode } = route.params;
    const navigation = useNavigation();

    // State
    const [history, setHistory] = useState([]);
    const [customerName, setCustomerName] = useState('');
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);

    // Pitch State
    const [pitchLoading, setPitchLoading] = useState(false);
    const [pitch, setPitch] = useState(null);
    const [pitchId, setPitchId] = useState(null);
    const [feedbackGiven, setFeedbackGiven] = useState(false);

    // Accordion State
    const [expandedOrder, setExpandedOrder] = useState(null);

    // Chart State
    const [chartVisible, setChartVisible] = useState(false);
    const [chartData, setChartData] = useState(null);
    const [chartLoading, setChartLoading] = useState(false);

    // Initial Load
    useEffect(() => {
        loadCustomerData();
    }, []);

    const loadCustomerData = async () => {
        setLoading(true);
        try {
            const result = await getCustomer(cardCode);
            if (result) {
                if (result.history) setHistory(result.history);
                if (result.customer_name) setCustomerName(result.customer_name);
                if (result.details) setDetails(result.details);
            }
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    // Pitch Handling
    const handleGeneratePitch = async () => {
        setPitchLoading(true);
        setPitch(null);
        setPitchId(null);
        setFeedbackGiven(false);
        try {
            const result = await generatePitch(cardCode, "");
            if (result && result.pitch) {
                setPitch(result.pitch);
                setPitchId(result.pitch_id);
            }
        } catch (e) {
            console.error(e);
        }
        setPitchLoading(false);
    };

    const toggleAccordion = (index) => {
        setExpandedOrder(expandedOrder === index ? null : index);
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    };

    const loadSalesTrend = async () => {
        setChartLoading(true);
        setChartVisible(true);

        // Trim cardCode to avoid url issues
        const cleanCardCode = cardCode ? cardCode.trim() : "";
        const data = await getCustomerTrends(cleanCardCode);

        if (data) {
            setChartData(data); // Sets data OR error
        }
        setChartLoading(false);
    };

    // Mock Data for UI (Extra information not yet in API)
    const recommendedProducts = [
        { id: 1, name: 'Arroz Fantástico 5kg', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDaBGyYZ797w5mpVaM48JiojcnPjWPm3A3iKMUQrL-jY6g5dxLj0O6m6L0bXKTGJjqC0aDQFlM-jV1sdr6QnUlki55bu9M4YREE4q-B3TCdHktwGFKV2DIeAJVpushM6l6gv2gc5Oe_-SnXjb9PbA6cT-jcBgxlKo9v2UYWPhD4PnNkLZUU_UxnTidW5RC2ltS9AAtBi_q_q3Y2v5hFIaeyRgdtCCyJDj86WgQT1RPxoK7JH15fDZtqttC53WcQXl8iIhcBm1kmBeA', tag: 'Alta Demanda', tagColor: 'green' },
        { id: 2, name: 'Feijão Carioca 1kg', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC-Ct6an2BPwElGmXICXaw-SzdzVUGi3G9xOte-gKQ4LdZh6b0t4g09kgZGEb-mU9yoBRxD1VmGi5UrF-b6KtmPldiQbh80E3uiS_pfZV-ZCEvbK3QkV0mwQPg6AkLAsMUrHR_fbHs6ekIi7CVKgOgqQhvv2KC_3Uo1RkUfmHjs5kwSFqxqcgDJk-umdSXUcf1_Kib-1fTeKPUEZ7osMa7o-n_SwqJE0CX5WuA14Ta5dex4mO7bXMIQ9QCdwIJXQvX0xrKnrAHCf2I', tag: 'Em Oferta', tagColor: 'orange' },
        { id: 3, name: 'Macarrão Espaguete', img: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC827GDJxzdol0EaLgRlIVVTpgTPLCnwnn-h1qVXU2AK9QFkAifbZwI1ni9YMgAByY4tajhYCap0-3iNmjXBuwrMQMipc9YTM47X_5t-bq5mzORoBNub3Ar9nDnTF03GVv1Yc7sNdW85j-icvgc_owmmzaJ4xugGNe99ZJJqI6NaD2Xs1-U8DwzUuDXLGLRUn6gpQUEFydm6Jmt_WS3bnIC7AN2asZQssF9epqIOso28yaOOmSX2fUbh2GMhLO86hlLn_ZkiOFw2aI', tag: 'Reposição', tagColor: 'blue' },
    ];

    return (
        <SafeAreaView style={tw`flex-1 bg-background-light dark:bg-black`}>


            <ScrollView contentContainerStyle={tw`pb-32`} showsVerticalScrollIndicator={false}>

                {/* Profile Card */}
                <View style={tw`px-4 pt-4`}>
                    <View style={tw`bg-white dark:bg-surface-dark rounded-2xl p-5 shadow-sm`}>
                        <View style={tw`flex-row items-center gap-4 mb-6`}>
                            <View style={tw`w-16 h-16 rounded-full bg-gray-200 justify-center items-center border border-gray-100`}>
                                <Icon name="person" size={40} color="#9CA3AF" />
                            </View>
                            <View style={tw`flex-1`}>
                                <Text style={tw`text-xl font-bold text-gray-900 dark:text-white leading-tight`}>
                                    {customerName || 'Carregando...'}
                                </Text>
                                <Text style={tw`text-sm text-gray-500 mt-1`}>
                                    {details?.AtivoDesde ? `Cliente Ativo desde ${details.AtivoDesde}` : 'Carregando...'}
                                </Text>
                            </View>
                        </View>

                        <View style={tw`flex-row justify-between border-t border-gray-100 pt-4 px-4`}>
                            <TouchableOpacity
                                style={tw`items-center gap-1 opacity-${details?.Telefone ? '100' : '50'}`}
                                onPress={() => details?.Telefone && Linking.openURL(`tel:${details.Telefone.replace(/\D/g, '')}`)}
                                disabled={!details?.Telefone}
                            >
                                <View style={tw`w-10 h-10 rounded-full bg-blue-50 items-center justify-center`}>
                                    <Icon name="call" size={20} color="#2563eb" />
                                </View>
                                <Text style={tw`text-xs text-primary font-medium`}>Ligar</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={tw`items-center gap-1 opacity-${details?.Email ? '100' : '50'}`}
                                onPress={() => details?.Email && Linking.openURL(`mailto:${details.Email}`)}
                                disabled={!details?.Email}
                            >
                                <View style={tw`w-10 h-10 rounded-full bg-blue-50 items-center justify-center`}>
                                    <Icon name="email" size={20} color="#2563eb" />
                                </View>
                                <Text style={tw`text-xs text-primary font-medium`}>E-mail</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={tw`items-center gap-1 opacity-${details?.Telefone ? '100' : '50'}`}
                                onPress={() => {
                                    if (details?.Telefone) {
                                        const cleanPhone = details.Telefone.replace(/\D/g, '');
                                        // Supports both Web (wa.me) and Mobile (automatically handled by browser/OS intents)
                                        // Using wa.me is more universal for cross-platform (Web + Mobile App)
                                        // Prefix 55 is assumed for Brazil if not present, but safer to just use what we have or append if specific logic needed.
                                        // Assuming local numbers might need country code. Let's append 55 if length is 10 or 11 (standard BR).
                                        let finalPhone = cleanPhone;
                                        if (cleanPhone.length >= 10 && cleanPhone.length <= 11) {
                                            finalPhone = '55' + cleanPhone;
                                        }
                                        Linking.openURL(`https://wa.me/${finalPhone}`);
                                    }
                                }}
                                disabled={!details?.Telefone}
                            >
                                <View style={tw`w-10 h-10 rounded-full bg-green-50 items-center justify-center`}>
                                    <Icon name="whatsapp" size={24} color="#25D366" />
                                </View>
                                <Text style={tw`text-xs text-primary font-medium`}>WhatsApp</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>

                {/* Contact Info */}
                <View style={tw`px-5 mt-6`}>
                    <Text style={tw`text-lg font-bold mb-2 text-gray-900 dark:text-white`}>Informações de Contato</Text>
                    <View style={tw`gap-1`}>
                        <Text style={tw`text-[15px] text-gray-700 dark:text-gray-300`}>
                            <Text style={tw`font-semibold text-gray-900 dark:text-white`}>Telefone: </Text>{details?.Telefone || 'Não informado'}
                        </Text>
                        <Text style={tw`text-[15px] text-gray-700 dark:text-gray-300`}>
                            <Text style={tw`font-semibold text-gray-900 dark:text-white`}>E-mail: </Text>{details?.Email ? details.Email.toLowerCase() : 'Não informado'}
                        </Text>
                        <Text style={tw`text-[15px] text-gray-700 dark:text-gray-300`}>
                            <Text style={tw`font-semibold text-gray-900 dark:text-white`}>Endereço: </Text>{details?.Endereco || 'Não informado'}
                        </Text>
                    </View>
                </View>

                {/* Sales Trends & Pitch */}
                <View style={tw`px-5 mt-6`}>
                    <View style={tw`flex-row items-center justify-between mb-2`}>
                        <Text style={tw`text-lg font-bold text-gray-900 dark:text-white`}>Tendências de Vendas</Text>
                        <TouchableOpacity
                            style={tw`bg-[#F05527] px-3 py-1.5 rounded-full flex-row items-center gap-1 shadow-sm`}
                            onPress={handleGeneratePitch}
                            disabled={pitchLoading}
                        >
                            {pitchLoading ? (
                                <ActivityIndicator size="small" color="white" />
                            ) : (
                                <>
                                    <Icon name="auto_awesome" size={14} color="white" />
                                    <Text style={tw`text-white text-[12px] font-bold`}>Gerar Pitch IA</Text>
                                </>
                            )}
                        </TouchableOpacity>
                    </View>

                    <View style={tw`bg-white dark:bg-surface-dark rounded-lg p-3 flex-row items-center gap-4 shadow-sm border border-gray-100 dark:border-gray-800`}>
                        <Text style={tw`text-[14px] text-gray-600 dark:text-gray-300 flex-1 leading-snug`}>
                            Tendência de vendas nos últimos 6 meses: arroz, feijão e massas.
                        </Text>
                        <TouchableOpacity
                            style={tw`w-24 h-12 justify-end gap-1 flex-row items-end pb-1`}
                            onPress={loadSalesTrend}
                        >
                            {/* Mini Bar Chart Placeholder (Clickable) */}
                            <View style={tw`w-2 h-4 bg-blue-200 rounded-sm`} />
                            <View style={tw`w-2 h-6 bg-blue-300 rounded-sm`} />
                            <View style={tw`w-2 h-5 bg-blue-200 rounded-sm`} />
                            <View style={tw`w-2 h-8 bg-blue-500 rounded-sm`} />
                            <View style={tw`w-2 h-10 bg-[#10B981] rounded-sm`} />
                        </TouchableOpacity>
                    </View>

                    {/* AI Pitch Result */}
                    {pitch && (
                        <View style={tw`mt-4 bg-indigo-50 p-4 rounded-xl border border-indigo-100`}>
                            <Text style={tw`font-bold text-indigo-700 mb-2`}>🤖 Sugestão da Mari IA:</Text>
                            <Text style={tw`text-gray-800 text-sm leading-relaxed mb-3`}>{pitch}</Text>

                            {!feedbackGiven ? (
                                <View style={tw`flex-row gap-3 mt-2`}>
                                    <TouchableOpacity style={tw`bg-white px-3 py-1.5 rounded-full border border-gray-200 flex-row items-center gap-1`} onPress={() => { setFeedbackGiven(true); sendPitchFeedback(pitchId, 'useful'); }}>
                                        <Text>👍 Útil</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity style={tw`bg-green-100 px-3 py-1.5 rounded-full border border-green-200 flex-row items-center gap-1`} onPress={() => { setFeedbackGiven(true); sendPitchFeedback(pitchId, 'sold'); }}>
                                        <Text style={tw`font-bold text-green-800`}>💰 Vendi!</Text>
                                    </TouchableOpacity>
                                </View>
                            ) : (
                                <Text style={tw`text-xs text-indigo-500 font-bold text-center`}>Feedback enviado!</Text>
                            )}
                        </View>
                    )}
                </View>

                {/* History Accordion */}
                <View style={tw`px-5 mt-6`}>
                    <Text style={tw`text-lg font-bold mb-2 text-gray-900 dark:text-white`}>Histórico de Compras Recentes</Text>
                    {loading ? (
                        <ActivityIndicator color="#1A2F5A" style={tw`mt-4`} />
                    ) : (
                        <View style={tw`gap-4`}>
                            {history.length === 0 && <Text style={tw`text-gray-400`}>Nenhum histórico encontrado.</Text>}
                            {history.slice(0, 5).map((item, index) => (
                                <View key={index} style={tw`bg-white dark:bg-surface-dark rounded-xl shadow-sm overflow-hidden`}>
                                    <TouchableOpacity
                                        style={tw`flex-row justify-between items-center p-3 cursor-pointer`}
                                        onPress={() => toggleAccordion(index)}
                                    >
                                        <View style={tw`flex-1`}>
                                            <View style={tw`flex-row items-center gap-2 mb-0.5`}>
                                                <Text style={tw`font-semibold text-[15px] text-gray-900 dark:text-white`}>
                                                    Doc: {item.document_number}
                                                </Text>
                                                <View style={tw`bg-green-100 px-1.5 py-0.5 rounded`}>
                                                    <Text style={tw`text-[10px] text-green-700 font-bold`}>
                                                        {item.status || 'Faturado'}
                                                    </Text>
                                                </View>
                                            </View>
                                            <Text style={tw`text-xs text-gray-500`}>
                                                {item.date ? new Date(item.date).toLocaleDateString('pt-BR') : '-'}
                                            </Text>
                                        </View>
                                        <View style={tw`items-end`}>
                                            <Text style={tw`font-bold text-gray-900 dark:text-white text-[15px]`}>
                                                {formatCurrency(item.total_value)}
                                            </Text>
                                            <Icon
                                                name={expandedOrder === index ? "expand_less" : "expand_more"}
                                                size={20}
                                                color="#9CA3AF"
                                            />
                                        </View>
                                    </TouchableOpacity>

                                    {/* Expanded Items */}
                                    {expandedOrder === index && (
                                        <View style={tw`px-3 pb-3 pt-1 border-t border-gray-100 bg-gray-50`}>
                                            <View style={tw`flex-row justify-between items-center mb-2 mt-1`}>
                                                <Text style={tw`text-[10px] font-semibold text-primary uppercase tracking-wider`}>Itens do Pedido</Text>
                                            </View>
                                            <View style={tw`gap-2`}>
                                                {item.items && item.items.map((prod, pIndex) => (
                                                    <View key={pIndex} style={tw`flex-row justify-between items-start`}>
                                                        <View style={tw`flex-1 pr-2`}>
                                                            <Text style={tw`text-[11px] font-medium text-gray-800 leading-tight`}>{prod.Nome_Produto}</Text>
                                                            <Text style={tw`text-[10px] text-gray-500`}>Qtd: {prod.Quantidade}</Text>
                                                        </View>
                                                        <Text style={tw`text-[11px] font-semibold text-green-700`}>{formatCurrency(prod.Valor_Liquido)}</Text>
                                                    </View>
                                                ))}
                                            </View>
                                            <View style={tw`mt-3 pt-2 border-t border-gray-200 items-end`}>
                                                <TouchableOpacity style={tw`flex-row items-center gap-1`}>
                                                    <Icon name="replay" size={14} color="#1A2F5A" />
                                                    <Text style={tw`text-[11px] font-medium text-primary`}>Repetir Pedido</Text>
                                                </TouchableOpacity>
                                            </View>
                                        </View>
                                    )}
                                </View>
                            ))}
                        </View>
                    )}
                </View>

                {/* Recommended Products Carousel */}
                <View style={tw`mt-6 mb-4`}>
                    <View style={tw`px-5 header flex-row items-center gap-2 mb-3`}>
                        <Text style={tw`text-lg font-bold text-gray-900 dark:text-white`}>Produtos Recomendados</Text>
                        <View style={tw`bg-indigo-100 px-2 py-0.5 rounded-full`}>
                            <Text style={tw`text-[10px] text-indigo-700 font-bold uppercase`}>MARI IA</Text>
                        </View>
                    </View>

                    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={tw`px-5 gap-4`}>
                        {recommendedProducts.map((prod) => (
                            <View key={prod.id} style={tw`w-[140px] bg-white rounded-xl p-3 shadow-sm border border-gray-100 justify-between`}>
                                <View style={tw`w-full h-24 bg-gray-50 rounded-lg mb-2 overflow-hidden items-center justify-center`}>
                                    <Image
                                        source={{ uri: prod.img }}
                                        style={tw`w-full h-full`}
                                        resizeMode="contain"
                                    />
                                </View>
                                <View>
                                    <Text style={tw`text-[13px] font-semibold text-gray-900 leading-tight mb-1`} numberOfLines={2}>{prod.name}</Text>
                                    <View style={tw`bg-${prod.tagColor}-100 self-start px-1.5 py-0.5 rounded`}>
                                        <Text style={tw`text-[10px] font-bold text-${prod.tagColor}-700`}>{prod.tag}</Text>
                                    </View>
                                </View>
                            </View>
                        ))}
                    </ScrollView>
                </View>

                {/* Footer Brand */}
                <View style={tw`items-center py-6 opacity-60 mb-10`}>
                    <View style={tw`flex-row items-center gap-2 mb-1`}>
                        <View style={tw`w-6 h-6 bg-orange-500 rounded-full items-center justify-center`}>
                            <Text style={tw`text-white font-bold text-xs`}>F</Text>
                        </View>
                        <Text style={tw`font-bold text-sm text-gray-900 dark:text-white`}>Fantástico Alimentos</Text>
                    </View>
                    <Text style={tw`text-[10px] text-gray-500`}>Powered by AI</Text>
                </View>

                {/* Static Bottom Actions (Scrolls with content) */}
                <View style={tw`w-full bg-white dark:bg-surface-dark px-4 pt-4 pb-8 border-t border-gray-200 dark:border-gray-800 flex-row gap-3`}>
                    <TouchableOpacity style={tw`flex-1 bg-brand-navy py-3 rounded-xl items-center shadow-md active:opacity-90`}>
                        <Text style={tw`text-white font-semibold text-[15px]`}>Contatar Cliente</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={tw`flex-1 bg-brand-navy py-3 rounded-xl items-center shadow-md active:opacity-90`}>
                        <Text style={tw`text-white font-semibold text-[15px]`}>Criar Novo Pedido</Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>

            {/* Sales Trend Modal */}
            <Modal
                animationType="slide"
                transparent={true}
                visible={chartVisible}
                onRequestClose={() => setChartVisible(false)}
            >
                <View style={tw`flex-1 justify-end bg-black/50`}>
                    <View style={tw`bg-white dark:bg-surface-dark rounded-t-3xl h-[60%] p-5`}>
                        <View style={tw`flex-row justify-between items-center mb-6`}>
                            <Text style={tw`text-xl font-bold text-gray-900 dark:text-white`}>Tendência de Vendas (6 Meses)</Text>
                            <TouchableOpacity onPress={() => setChartVisible(false)} style={tw`p-2 bg-gray-100 rounded-full`}>
                                <Icon name="close" size={20} color="#374151" />
                            </TouchableOpacity>
                        </View>

                        {chartLoading ? (
                            <View style={tw`flex-1 justify-center items-center`}>
                                <ActivityIndicator size="large" color="#1A2F5A" />
                                <Text style={tw`mt-4 text-gray-500`}>Carregando dados...</Text>
                            </View>
                        ) : chartData && chartData.labels ? (
                            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                                <View>
                                    <LineChart
                                        data={{
                                            labels: chartData.labels,
                                            datasets: chartData.datasets.map(ds => ({
                                                data: ds.data,
                                                color: (opacity = 1) => ds.color || `rgba(26, 47, 90, ${opacity})`,
                                                strokeWidth: 2
                                            })),
                                            legend: chartData.datasets.map(ds => ds.name)
                                        }}
                                        width={Dimensions.get("window").width + 100} // Horizontal scroll
                                        height={300}
                                        yAxisLabel="R$ "
                                        yAxisInterval={1}
                                        chartConfig={{
                                            backgroundColor: "#ffffff",
                                            backgroundGradientFrom: "#ffffff",
                                            backgroundGradientTo: "#ffffff",
                                            decimalPlaces: 0,
                                            color: (opacity = 1) => `rgba(26, 47, 90, ${opacity})`,
                                            labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                                            style: {
                                                borderRadius: 16
                                            },
                                            propsForDots: {
                                                r: "4",
                                                strokeWidth: "2",
                                                stroke: "#ffa726"
                                            }
                                        }}
                                        bezier
                                        style={{
                                            marginVertical: 8,
                                            borderRadius: 16
                                        }}
                                    />
                                    <Text style={tw`text-xs text-center text-gray-400 mt-2`}>Valores em Reais (R$)</Text>
                                </View>
                            </ScrollView>
                        ) : (
                            <View style={tw`flex-1 justify-center items-center px-4`}>
                                <Text style={tw`text-gray-500 text-center mb-2`}>Dados insuficientes para gerar o gráfico.</Text>
                                {chartData && chartData.error && (
                                    <Text style={tw`text-red-500 text-xs text-center mt-2`}>Erro Técnico: {chartData.error}</Text>
                                )}
                            </View>
                        )}
                    </View>
                </View>
            </Modal>
        </SafeAreaView>
    );
}
