import React from 'react';
import { Platform, Text, View, Image } from 'react-native';
import { MaterialIcons, FontAwesome } from '@expo/vector-icons';

// Mapping for specific icons that might have different names or issues
const ICON_MAPPING = {
    // Native (Expo key) : Web (Ligature text)
    'auto_awesome': { native: 'stars', web: 'auto_awesome' },
    'expand_more': { native: 'keyboard-arrow-down', web: 'expand_more' },
    'expand_less': { native: 'keyboard-arrow-up', web: 'expand_less' },
};

export default function Icon({ name, size = 24, color = '#000', style }) {

    // Special handling for WhatsApp (Brand Icon)
    if (name === 'whatsapp') {
        if (Platform.OS === 'web') {
            return (
                <View style={[style, { width: size, height: size }]}>
                    <Image
                        source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg' }}
                        style={{ width: size, height: size, resizeMode: 'contain' }}
                        accessibilityLabel="WhatsApp"
                    />
                </View>
            );
        }
        return <FontAwesome name="whatsapp" size={size} color={color} style={style} />;
    }

    let finalName = name;
    let isMaterial = true;

    // Handle mapping
    if (ICON_MAPPING[name]) {
        // Warning: ICON_MAPPING structure in this file was previously inconsistent. 
        // Adapting to simple string mapping or object mapping.
        const mapping = ICON_MAPPING[name];
        if (typeof mapping === 'string') {
            finalName = mapping;
        } else if (Platform.OS === 'web') {
            finalName = mapping.web;
        } else {
            finalName = mapping.native;
        }
    }

    if (Platform.OS === 'web') {
        return (
            <Text
                style={[{
                    fontFamily: 'Material Icons',
                    fontSize: size,
                    color: color,
                    fontWeight: 'normal',
                    fontStyle: 'normal',
                    lineHeight: size,
                    letterSpacing: 'normal',
                    textTransform: 'none',
                    whiteSpace: 'nowrap',
                    wordWrap: 'normal',
                    WebkitFontSmoothing: 'antialiased',
                }, style]}
                selectable={false}
            >
                {finalName}
            </Text>
        );
    }

    // On native, use the regular MaterialIcons component
    return <MaterialIcons name={finalName} size={size} color={color} style={style} />;
}
