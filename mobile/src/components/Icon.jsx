import React from 'react';
import { Platform, Text, View, Image } from 'react-native';
import { MaterialIcons, FontAwesome } from '@expo/vector-icons';

// Mapping for specific icons that might have different names or issues
// Now supports 'family' property to switch icon sets
// Mapping for specific icons that might have different names or issues
// Now supports 'family' property to switch icon sets
const ICON_MAPPING = {
    // PitchCard Icons
    'shopping_cart': { native: 'shopping-cart', web: 'shopping_cart' }, // Material often prefers dashes
    'record_voice_over': { native: 'record-voice-over', web: 'record_voice_over' },
    'content_copy': { native: 'content-copy', web: 'content_copy' },
    'info': { native: 'info', web: 'info' }, // 'info' usually works, trying direct
    'thumb_up': { native: 'thumbs-up', family: 'FontAwesome', web: 'thumbs-up' }, // Material 'thumb-up' can be flaky, FA 'thumbs-up' is safe
    'check_circle': { native: 'check-circle', family: 'FontAwesome', web: 'check-circle' },

    // Others
    'auto_awesome': { native: 'auto-awesome', web: 'auto_awesome' },
    'expand_more': { native: 'keyboard-arrow-down', web: 'expand_more' },
    'expand_less': { native: 'keyboard-arrow-up', web: 'expand_less' },
    'local_shipping': { native: 'truck', family: 'FontAwesome', web: 'truck' }, // Material 'local-shipping' -> FA 'truck'
    'history': { native: 'history', family: 'FontAwesome', web: 'history' },
    'shuffle': { native: 'random', family: 'FontAwesome', web: 'random' }, // FA 'random' is shuffle equivalent
    'person': { native: 'user', family: 'FontAwesome', web: 'user' },
    'call': { native: 'phone', family: 'FontAwesome', web: 'phone' },
    'email': { native: 'envelope', family: 'FontAwesome', web: 'envelope' },
    'close': { native: 'close', family: 'FontAwesome', web: 'close' },
    'chevron_left': { native: 'chevron-left', family: 'FontAwesome', web: 'chevron-left' },
    'chevron_right': { native: 'chevron-right', family: 'FontAwesome', web: 'chevron-right' },
    'receipt_long': { native: 'list-alt', family: 'FontAwesome', web: 'list-alt' },
    'emoji_events': { native: 'trophy', family: 'FontAwesome', web: 'trophy' },
    'forum': { native: 'forum', web: 'forum' },
    'smart_toy': { native: 'smart-toy', web: 'smart_toy' },
    'assistant': { native: 'assistant', web: 'assistant' },
    'bar_chart': { native: 'bar-chart', web: 'bar_chart' },
    'analytics': { native: 'analytics', web: 'analytics' },
    'chat_bubble': { native: 'chat-bubble', web: 'chat_bubble' },
    'chat': { native: 'chat-bubble', web: 'chat_bubble' },

    // Chat Screen Icons
    'delete_outline': { native: 'delete-outline', web: 'delete_outline' },
    'add': { native: 'add', web: 'add' },
    'sticky_note_2': { native: 'sticky-note-2', web: 'sticky_note_2' },
    'stop': { native: 'stop', web: 'stop' },
    'send': { native: 'send', web: 'send' },
    'mic': { native: 'mic', web: 'mic' }
};

export default function Icon({ name, size = 24, color = '#000', style }) {
    // Inject Fonts for Web
    React.useEffect(() => {
        if (Platform.OS === 'web') {
            const fontId = 'mariia-web-fonts';
            if (!document.getElementById(fontId)) {
                // Use standard Google Fonts import for Material Icons + FontAwesome CDN
                const css = `
                    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
                    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css');
                `;
                const styleEl = document.createElement('style');
                styleEl.id = fontId;
                styleEl.type = 'text/css';
                styleEl.appendChild(document.createTextNode(css));
                document.head.appendChild(styleEl);
            }
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
            if (mapping.family === 'FontAwesome') {
                finalName = mapping.web || mapping.native || name;
                family = 'FontAwesome';
            } else {
                finalName = mapping.web || name;
            }
        } else {
            finalName = mapping.native || name;
            if (mapping.family) {
                family = mapping.family;
            }
        }
    }

    if (Platform.OS === 'web') {
        const domStyle = {
            fontSize: size,
            color: color,
            width: size,
            height: size,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            ...style
        };

        if (family === 'FontAwesome') {
            // FontAwesome: usage <i class="fa fa-name"></i>
            return (
                <View style={[{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }, style]}>
                    <i className={`fa fa-${finalName}`} style={{ fontSize: size, color: color }} aria-hidden="true"></i>
                </View>
            );
        }

        // Material Icons: usage <span class="material-icons">name</span>
        return (
            <View style={[{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }, style]}>
                <span className="material-icons" style={{ fontSize: size, color: color, userSelect: 'none' }}>
                    {finalName}
                </span>
            </View>
        );
    }

    if (family === 'FontAwesome') {
        return <FontAwesome name={finalName} size={size} color={color} style={style} />;
    }

    return <MaterialIcons name={finalName} size={size} color={color} style={style} />;
}
