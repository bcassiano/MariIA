import React from 'react';
import { Platform, Text, View, Image } from 'react-native';
import { MaterialIcons, FontAwesome } from '@expo/vector-icons';

// Mapping for specific icons that might have different names or issues
// Now supports 'family' property to switch icon sets
const ICON_MAPPING = {
    // PitchCard Icons
    'shopping_cart': { native: 'shopping-cart', web: 'shopping_cart' }, // Material often prefers dashes
    'record_voice_over': { native: 'record-voice-over', web: 'record_voice_over' },
    'content_copy': { native: 'content-copy', web: 'content_copy' },
    'info': { native: 'info', web: 'info' }, // 'info' usually works, trying direct
    'thumb_up': { native: 'thumbs-up', family: 'FontAwesome', web: 'thumb_up' }, // Material 'thumb-up' can be flaky, FA 'thumbs-up' is safe
    'check_circle': { native: 'check-circle', family: 'FontAwesome', web: 'check_circle' },

    // Others
    'auto_awesome': { native: 'stars', web: 'auto_awesome' },
    'expand_more': { native: 'keyboard-arrow-down', web: 'expand_more' },
    'expand_less': { native: 'keyboard-arrow-up', web: 'expand_less' },
    'local_shipping': { native: 'truck', family: 'FontAwesome', web: 'local_shipping' }, // Material 'local-shipping' -> FA 'truck'
    'history': { native: 'history', family: 'FontAwesome', web: 'history' },
    'shuffle': { native: 'random', family: 'FontAwesome', web: 'shuffle' }, // FA 'random' is shuffle equivalent
    'person': { native: 'user', family: 'FontAwesome', web: 'person' },
    'call': { native: 'phone', family: 'FontAwesome', web: 'call' },
    'email': { native: 'envelope', family: 'FontAwesome', web: 'email' },
    'close': { native: 'close', family: 'FontAwesome', web: 'close' },
    'chevron_left': { native: 'chevron-left', family: 'FontAwesome', web: 'chevron_left' },
    'chevron_left': { native: 'chevron-left', family: 'FontAwesome', web: 'chevron_left' },
    'chevron_right': { native: 'chevron-right', family: 'FontAwesome', web: 'chevron_right' },
    'receipt_long': { native: 'list-alt', family: 'FontAwesome', web: 'receipt_long' },
    'emoji_events': { native: 'trophy', family: 'FontAwesome', web: 'emoji_events' },
    'forum': { native: 'forum', web: 'forum' },
    'smart_toy': { native: 'smart-toy', web: 'smart_toy' }
};

export default function Icon({ name, size = 24, color = '#000', style }) {
    // Add font loading for Web
    React.useEffect(() => {
        if (Platform.OS === 'web') {
            const fontFace = `
                @font-face {
                    font-family: 'Material Icons';
                    font-style: normal;
                    font-weight: 400;
                    src: url(https://fonts.gstatic.com/s/materialicons/v140/flUhRq6tzZclQEJ-Vdg-IuiaDsNcIhQ8tQ.woff2) format('woff2');
                }
            `;
            const style = document.createElement('style');
            style.type = 'text/css';
            style.appendChild(document.createTextNode(fontFace));
            document.head.appendChild(style);
        }
    }, []);

    // Special handling for WhatsApp
    if (name === 'whatsapp') {
        if (Platform.OS === 'web') {
            return (
                <View style={[style, { width: size, height: size }]}>
                    <Image
                        source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg' }}
                        style={{ width: size, height: size }}
                        resizeMode="contain"
                        accessibilityLabel="WhatsApp"
                    />
                </View>
            );
        }
        return <FontAwesome name="whatsapp" size={size} color={color} style={style} />;
    }

    let finalName = name;
    let family = 'MaterialIcons';

    // Handle mapping
    if (ICON_MAPPING[name]) {
        const mapping = ICON_MAPPING[name];
        if (Platform.OS === 'web') {
            finalName = mapping.web || name;
            // Web usually relies on Material Icons font being loaded with underscores
        } else {
            finalName = mapping.native || name;
            if (mapping.family) {
                family = mapping.family;
            }
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
                {name.replace(/-/g, '_')} {/* Web Font usually expects underscores */}
            </Text>
        );
    }

    // Native Render
    if (family === 'FontAwesome') {
        return <FontAwesome name={finalName} size={size} color={color} style={style} />;
    }

    return <MaterialIcons name={finalName} size={size} color={color} style={style} />;
}
