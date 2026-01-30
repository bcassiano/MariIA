import 'react-native-gesture-handler';
import React from 'react';
import { Platform, TouchableOpacity, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import * as Font from 'expo-font';
import { MaterialIcons } from '@expo/vector-icons';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import HomeScreen from './src/screens/HomeScreen';
import CustomerScreen from './src/screens/CustomerScreen';
import ChatScreen from './src/screens/ChatScreen';

const Stack = createStackNavigator();

export default function App() {
    // State for font loading
    const [fontsLoaded, setFontsLoaded] = React.useState(false);

    React.useEffect(() => {
        async function loadFonts() {
            try {
                // Load fonts for Web and Mobile
                await Font.loadAsync({
                    ...MaterialIcons.font,
                });

                if (Platform.OS === 'web') {
                    const style = document.createElement('style');
                    style.textContent = `
                        html, body, #root {
                            height: 100%;
                            overflow-y: auto;
                            -webkit-overflow-scrolling: touch;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                        }
                     `;
                    document.head.appendChild(style);
                }
            } catch (e) {
                console.warn("Error loading fonts", e);
            } finally {
                setFontsLoaded(true);
            }
        }
        loadFonts();
    }, []);

    if (!fontsLoaded) {
        return null; // Or a Loading indicator
    }

    return (
        <SafeAreaProvider>
            <NavigationContainer>
                <Stack.Navigator
                    screenOptions={{
                        cardStyle: { flex: 1 },
                        headerStyle: {
                            backgroundColor: '#1A2F5A',
                            elevation: 0, // Remove shadow for cleaner look
                        },
                        headerTintColor: '#fff',
                        headerTitleStyle: {
                            fontWeight: 'bold',
                            fontFamily: Platform.OS === 'web' ? 'sans-serif' : undefined,
                        },
                    }}
                >
                    <Stack.Screen
                        name="Home"
                        component={HomeScreen}
                        options={{
                            title: 'Mari IA',
                            headerTitleAlign: 'center',
                            headerTitleStyle: {
                                fontWeight: 'bold',
                                fontSize: Platform.OS === 'web' ? 24 : 20,
                                fontFamily: Platform.OS === 'web' ? 'sans-serif' : undefined,
                            },
                        }}
                    />
                    <Stack.Screen
                        name="Customer"
                        component={CustomerScreen}
                        options={{
                            headerShown: false,
                            title: 'Mari IA - Detalhes'
                        }}
                    />
                    <Stack.Screen
                        name="Chat"
                        component={ChatScreen}
                        options={{
                            headerShown: true,
                            title: 'Mari IA - Assistente',
                            headerTitleAlign: 'center'
                        }}
                    />
                </Stack.Navigator>
            </NavigationContainer>
        </SafeAreaProvider>
    );
}
