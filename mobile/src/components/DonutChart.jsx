import React from 'react';
import { View, Text } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';
import { create } from 'twrnc';

const tw = create(require('../../tailwind.config.js'));

export default function DonutChart({ positivated, nonPositivated, rate }) {
    const total = positivated + nonPositivated;

    // Evitar divisão por zero
    if (total === 0) {
        return (
            <View style={tw`items-center justify-center py-8`}>
                <Text style={tw`text-gray-500`}>Sem dados para exibir</Text>
            </View>
        );
    }

    const size = 260; // Tamanho total do SVG
    const strokeWidth = 28;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const positivatedPercentage = positivated / total;
    const positivatedOffset = circumference - (positivatedPercentage * circumference);
    const center = size / 2;

    return (
        <View style={tw`items-center justify-center w-full`}>
            <View style={{ width: size, height: size }}>
                <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                    <G transform={`rotate(-90, ${center}, ${center})`}>
                        {/* Background circle (não positivados) */}
                        <Circle
                            cx={center}
                            cy={center}
                            r={radius}
                            stroke="#FEE2E2" // Vermelho bem claro para fundo
                            strokeWidth={strokeWidth}
                            fill="transparent"
                        />
                        {/* Foreground circle (não positivados - restante) */}
                        <Circle
                            cx={center}
                            cy={center}
                            r={radius}
                            stroke="#EF4444" // Vermelho normal para parte não positivada (opcional, ou deixar só o verde sobre o cinza/vermelho claro)
                            strokeWidth={strokeWidth}
                            strokeDasharray={circumference}
                            strokeDashoffset={0} // Completo
                            fill="transparent"
                            opacity={0.3}
                        />
                        {/* Foreground circle (positivados) */}
                        <Circle
                            cx={center}
                            cy={center}
                            r={radius}
                            stroke="#16A34A" // Verde vibrante
                            strokeWidth={strokeWidth}
                            strokeDasharray={circumference}
                            strokeDashoffset={positivatedOffset}
                            strokeLinecap="round"
                            fill="transparent"
                        />
                    </G>
                </Svg>

                {/* Center text - Absolute em relação ao container do SVG */}
                <View style={[tw`absolute inset-0 items-center justify-center`]}>
                    <Text style={tw`text-5xl font-bold text-gray-800`}>{typeof rate === 'number' ? rate.toFixed(1) : rate}%</Text>
                    <Text style={tw`text-sm text-gray-500 font-medium uppercase tracking-wider mt-1`}>Positivação</Text>
                </View>
            </View>
        </View>
    );
}
