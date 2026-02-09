import React, { useState, useEffect, useCallback } from 'react';
import { Animated, Text, View, StyleSheet, Platform } from 'react-native';
import { create } from 'twrnc';

const tw = create(require('../../tailwind.config.js'));

let toastRef = null;

export const showToast = (message, type = 'success') => {
    if (toastRef) {
        toastRef(message, type);
    }
};

export default function Toast() {
    const [message, setMessage] = useState('');
    const [type, setType] = useState('success'); // 'success' | 'error' | 'info'
    const [visible, setVisible] = useState(false);
    const fadeAnim = useState(new Animated.Value(0))[0];

    const show = useCallback((msg, t) => {
        setMessage(msg);
        setType(t);
        setVisible(true);

        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
        }).start(() => {
            setTimeout(() => {
                hide();
            }, 3000);
        });
    }, [fadeAnim]);

    const hide = useCallback(() => {
        Animated.timing(fadeAnim, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
        }).start(() => {
            setVisible(false);
        });
    }, [fadeAnim]);

    useEffect(() => {
        toastRef = show;
        return () => {
            toastRef = null;
        };
    }, [show]);

    if (!visible) return null;

    const getBgColor = () => {
        switch (type) {
            case 'success': return 'bg-green-600';
            case 'error': return 'bg-red-600';
            case 'info': return 'bg-primary';
            default: return 'bg-gray-800';
        }
    };

    return (
        <Animated.View
            style={[
                tw`absolute bottom-20 left-6 right-6 p-4 rounded-xl shadow-lg z-[100] flex-row items-center ${getBgColor()}`,
                { opacity: fadeAnim, transform: [{ translateY: fadeAnim.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }] }
            ]}
        >
            <Text style={tw`text-white font-bold flex-1 text-center`}>{message}</Text>
        </Animated.View>
    );
}
