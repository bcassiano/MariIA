import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Clipboard, Alert } from 'react-native';
import { create } from 'twrnc';
import Icon from './Icon';

// Tailwind Config
const tw = create(require('../../tailwind.config.js'));

export default function PitchCard({ pitch, onFeedback }) {
    const [feedbackGiven, setFeedbackGiven] = useState(false);

    const handleCopy = () => {
        const pitchText = isStructured ? pitch.pitch_text : (typeof pitch === 'string' ? pitch : "Erro na análise.");
        Clipboard.setString(pitchText);
        Alert.alert('Copiado', 'Pitch copiado para a área de transferência!');
    };

    const handleFeedback = (type) => {
        setFeedbackGiven(true);
        if (onFeedback) {
            onFeedback(type);
        }
    };

    // Data derived from the 'pitch' prop (JSON object from AI)
    const isStructured = typeof pitch === 'object' && pitch !== null;
    const profileText = isStructured ? pitch.profile_summary : "Análise não disponível.";
    const frequencyText = isStructured ? pitch.frequency_assessment : "Análise não disponível.";
    const pitchText = isStructured ? pitch.pitch_text : (typeof pitch === 'string' ? pitch : "Erro na análise.");

    const reasons = isStructured && Array.isArray(pitch.reasons) && pitch.reasons.length > 0 ? pitch.reasons : [
        { title: "Análise", text: "Mari IA analisando histórico...", icon: "history" }
    ];
    const suggestedOrder = isStructured && Array.isArray(pitch.suggested_order) ? pitch.suggested_order : [];
    const motivation = isStructured ? pitch.motivation : "Boas vendas!";

    // Helper to bold text wrapped in **
    const renderStyledText = (text, style) => {
        if (!text) return null;
        const parts = String(text).split(/(\*\*.*?\*\*)/g);
        return (
            <Text style={style}>
                {parts.map((part, index) => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                        return <Text key={index} style={tw`font-bold text-gray-900`}>{part.slice(2, -2)}</Text>;
                    }
                    return part;
                })}
            </Text>
        );
    };

    // Helper clean quantity (removes text)
    const cleanQty = (qty) => {
        if (!qty) return 0;
        const num = parseFloat(String(qty).replace(/[^0-9.]/g, ''));
        return isNaN(num) ? 0 : num;
    };

    return (
        <View style={tw`bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden`}>

            {/* Header */}
            <View style={tw`bg-indigo-50 px-4 py-3 flex-row items-center gap-2 border-b border-indigo-100`}>
                <Icon name="auto_awesome" size={20} color="#4F46E5" />
                <Text style={tw`font-bold text-indigo-700 text-base`}>Sugestão da Mari IA</Text>
            </View>

            <View style={tw`p-4 gap-6`}>

                {/* 1. Perfil de Compra */}
                <View>
                    <View style={tw`flex-row items-center gap-2 mb-2`}>
                        <Icon name="shopping_cart" size={18} color="#EA580C" />
                        <Text style={tw`font-bold text-gray-600 text-[13px] uppercase`}>1. Perfil de Compra</Text>
                    </View>
                    {renderStyledText(profileText, tw`text-gray-600 text-[13px] leading-relaxed`)}
                </View>

                {/* 2. Frequência Média */}
                <View>
                    <View style={tw`flex-row items-center gap-2 mb-2`}>
                        <Icon name="event" size={18} color="#EA580C" />
                        <Text style={tw`font-bold text-gray-600 text-[13px] uppercase`}>2. Frequência Média</Text>
                    </View>
                    <View style={tw`bg-green-100 self-start px-2 py-0.5 rounded mb-2`}>
                        <Text style={tw`text-[10px] text-green-700 font-bold`}>Alta Recorrência</Text>
                    </View>
                    {renderStyledText(frequencyText, tw`text-gray-600 text-[13px] leading-relaxed`)}
                </View>

                {/* 3. Pitch de Venda (Highlighted Card) */}
                <View style={tw`rounded-xl p-1 bg-orange-50 border border-orange-100 shadow-sm`}>
                    <View style={tw`bg-white/60 rounded-lg p-4`}>
                        <View style={tw`flex-row justify-between items-center mb-3`}>
                            <View style={tw`flex-row items-center gap-2`}>
                                <Icon name="record_voice_over" size={20} color="#EA580C" />
                                <Text style={tw`font-bold text-orange-600 text-sm uppercase`}>Pitch de Venda</Text>
                            </View>
                            <TouchableOpacity onPress={() => {
                                Clipboard.setString(pitchText);
                                Alert.alert('Copiado', 'Pitch copiado para a área de transferência!');
                            }} style={tw`flex-row items-center gap-1 opacity-60`}>
                                <Icon name="content_copy" size={14} color="#374151" />
                                <Text style={tw`text-[10px] font-bold text-gray-700`}>Copiar</Text>
                            </TouchableOpacity>
                        </View>

                        <Text style={tw`text-gray-800 text-[14px] leading-relaxed italic mb-4`}>
                            "{pitchText}"
                        </Text>

                        <View style={tw`border-l-4 border-orange-500 pl-3 py-1 bg-orange-50 rounded-r-lg`}>
                            <Text style={tw`text-gray-600 text-[12px] italic`}>
                                "Dica: {["Use áudio para um toque mais pessoal.", "Confirme se o cliente viu a oferta.", "Pergunte sobre o estoque atual."][Math.floor(Math.random() * 3)]}"
                            </Text>
                        </View>
                    </View>

                    {/* SUGGESTED ORDER TABLE */}
                    {suggestedOrder.length > 0 ? (
                        <View style={tw`mt-4 bg-white rounded-lg p-3 border border-gray-200`}>
                            <View style={tw`flex-row items-center justify-between mb-2 border-b border-gray-100 pb-2`}>
                                <View style={tw`flex-row items-center gap-2`}>
                                    <Icon name="receipt_long" size={18} color="#15803d" />
                                    <Text style={tw`font-bold text-green-700 text-xs uppercase`}>Pedido ideal Mari IA</Text>
                                </View>
                                <TouchableOpacity
                                    style={tw`bg-accent-btn px-3 py-1.5 rounded-full flex-row items-center gap-1 shadow-sm`}
                                    onPress={() => Alert.alert('Sucesso', 'Pedido criado com sucesso!')}
                                >
                                    <Icon name="add_shopping_cart" size={14} color="white" />
                                    <Text style={tw`text-white text-[10px] font-bold`}>Criar Pedido</Text>
                                </TouchableOpacity>
                            </View>

                            <View style={tw`flex-row mb-1`}>
                                <Text style={tw`flex-1 text-[10px] font-bold text-gray-500`}>PRODUTO/SKU</Text>
                                <Text style={tw`w-12 text-[10px] font-bold text-gray-500 text-center`}>QTD</Text>
                            </View>

                            {suggestedOrder.map((item, idx) => {
                                const numericQty = cleanQty(item.quantity);

                                return (
                                    <View key={idx} style={tw`flex-row py-1.5 border-t border-gray-50 items-center`}>
                                        <View style={tw`flex-1 pr-2`}>
                                            <Text style={tw`text-[11px] font-bold text-gray-800 leading-tight`}>{item.product_name}</Text>
                                            <Text style={tw`text-[9px] text-gray-400`}>{item.sku}</Text>
                                        </View>
                                        <Text style={tw`w-12 text-[11px] font-bold text-gray-800 text-center`}>{numericQty}</Text>
                                    </View>
                                );
                            })}

                            <View style={tw`flex-row justify-end items-center mt-2 pt-2 border-t border-gray-200`}>
                                <Text style={tw`text-xs font-bold text-gray-600 mr-2`}>TOTAL (FD):</Text>
                                <Text style={tw`text-sm font-bold text-green-700`}>
                                    {suggestedOrder.reduce((acc, item) => {
                                        return acc + cleanQty(item.quantity);
                                    }, 0)}
                                </Text>
                            </View>
                        </View>
                    ) : (
                        <View style={tw`mt-4 bg-white/40 rounded-lg p-4 border border-dashed border-gray-300 items-center`}>
                            <Icon name="inventory_2" size={24} color="#9CA3AF" />
                            <Text style={tw`text-gray-500 text-[11px] mt-1 font-medium`}>Aguardando dados específicos de estoque...</Text>
                        </View>
                    )}
                </View>

                {/* MOTIVATION FOOTER */}
                {motivation && (
                    <View style={tw`bg-indigo-900 mx-4 mb-4 p-4 rounded-xl shadow-md border-l-4 border-yellow-400`}>
                        <View style={tw`flex-row items-center gap-3`}>
                            <Icon name="emoji_events" size={24} color="#FACC15" />
                            <Text style={tw`flex-1 text-white font-bold text-sm italic leading-snug`}>
                                "{motivation}"
                            </Text>
                        </View>
                    </View>
                )}

                {/* 4. Transparência */}
                <View>
                    <View style={tw`flex-row items-center gap-2 mb-3`}>
                        <Icon name="info" size={18} color="#3B82F6" />
                        <Text style={tw`font-bold text-blue-500 text-[12px] uppercase`}>Por que sugeri isso? (Transparência)</Text>
                    </View>

                    <View style={tw`gap-2`}>
                        {reasons.map((reason, idx) => (
                            <View key={idx} style={tw`flex-row gap-2`}>
                                <Icon name={reason.icon || "info"} size={14} color="#6B7280" style={tw`mt-0.5`} />
                                <Text style={tw`text-[11px] text-gray-500 flex-1 leading-snug`}>
                                    <Text style={tw`font-bold text-gray-700`}>{reason.title || "Dica"}: </Text>
                                    {reason.text || "Analisando histórico de consumo..."}
                                </Text>
                            </View>
                        ))}
                    </View>
                </View>

                {/* Feedback Buttons */}
                {!feedbackGiven ? (
                    <View style={tw`flex-row gap-3 mt-2 justify-end border-t border-gray-100 pt-3`}>
                        <TouchableOpacity style={tw`bg-white px-3 py-1.5 rounded-full border border-gray-200 flex-row items-center gap-1`} onPress={() => handleFeedback('useful')}>
                            <Icon name="thumb_up" size={14} color="#4B5563" />
                            <Text style={tw`text-xs font-medium text-gray-700`}>Útil</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={tw`bg-green-100 px-3 py-1.5 rounded-full border border-green-200 flex-row items-center gap-1`} onPress={() => handleFeedback('sold')}>
                            <Icon name="check_circle" size={14} color="#166534" />
                            <Text style={tw`text-xs font-bold text-green-800`}>Vendi!</Text>
                        </TouchableOpacity>
                    </View>
                ) : (
                    <Text style={tw`text-xs text-indigo-500 font-bold text-center mt-2`}>Obrigado pelo seu feedback!</Text>
                )}

                <View style={tw`mt-4 pt-4 border-t border-gray-100 items-center`}>
                    <Text style={tw`text-[10px] text-gray-400 text-center leading-tight`}>
                        A Mari IA pode cometer erros. As informações devem ser verificadas.
                    </Text>
                </View>

            </View>
        </View>
    );
}
