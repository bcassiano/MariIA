import 'react-native-gesture-handler';
import React from 'react';
import { Platform, TouchableOpacity, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import * as Font from 'expo-font';
import { MaterialIcons, FontAwesome } from '@expo/vector-icons';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import HomeScreen from './src/screens/HomeScreen';
import CustomerScreen from './src/screens/CustomerScreen';
import ChatScreen from './src/screens/ChatScreen';
import PortfolioScreen from './src/screens/PortfolioScreen';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Linking from 'expo-linking';

const Stack = createStackNavigator();

export default function App() {
    // State for font loading
    const [fontsLoaded, setFontsLoaded] = React.useState(false);
    const [sessionReady, setSessionReady] = React.useState(false);

    React.useEffect(() => {
        async function init() {
            try {
                // 1. Session Logic
                let userId = null;
                if (Platform.OS === 'web') {
                    const params = new URLSearchParams(window.location.search);
                    userId = params.get('user_id');
                } else {
                    const initialUrl = await Linking.getInitialURL();
                    if (initialUrl) {
                        const { queryParams } = Linking.parse(initialUrl);
                        userId = queryParams?.user_id;
                    }
                }

                // Se não houver user_id, usa vendedor padrão
                if (!userId) {
                    userId = 'V.vp - Renata Rodrigues'; // Vendedor padrão exato do banco
                    console.log("Session Init: No user_id provided, using default =", userId);
                } else {
                    console.log("Session Init: Found user_id =", userId);
                }

                await AsyncStorage.setItem('user_session_id', userId);

                // 2. Font Loading
                await Font.loadAsync({
                    ...MaterialIcons.font,
                    ...FontAwesome.font,
                });

                // 3. Web Styles
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
                console.warn("Error initializing app", e);
            } finally {
                setFontsLoaded(true);
                setSessionReady(true);
            }
        }
        init();
    }, []);

    if (!fontsLoaded || !sessionReady) {
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
                    <Stack.Screen
                        name="Portfolio"
                        component={PortfolioScreen}
                        options={{
                            headerShown: false,
                            title: 'Minha Carteira'
                        }}
                    />
                </Stack.Navigator>
            </NavigationContainer>
        </SafeAreaProvider>
    );
}
