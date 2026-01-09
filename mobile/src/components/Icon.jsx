import React from 'react';
import { Text, Platform } from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';

/**
 * Cross-platform icon component that uses:
 * - MaterialIcons from @expo/vector-icons on native
 * - Material Icons from Google Fonts on web (via CSS class)
 */
export default function Icon({ name, size = 24, color = '#000' }) {
    if (Platform.OS === 'web') {
        // On web, use the Material Icons font loaded via Google Fonts in index.html
        return (
            <Text
                style={{
                    fontFamily: 'Material Icons',
                    fontSize: size,
                    color: color,
                    // These styles are required for Material Icons to work properly
                    fontWeight: 'normal',
                    fontStyle: 'normal',
                    lineHeight: size,
                    letterSpacing: 'normal',
                    textTransform: 'none',
                    whiteSpace: 'nowrap',
                    wordWrap: 'normal',
                    WebkitFontSmoothing: 'antialiased',
                }}
                selectable={false}
            >
                {name}
            </Text>
        );
    }

    // On native, use the regular MaterialIcons component
    return <MaterialIcons name={name} size={size} color={color} />;
}

// Map common icon names (MaterialIcons uses underscores, Web uses spaces/underscores)
// This component expects the standard MaterialIcons name format (e.g., 'call', 'email', 'chat')
