import 'react-native-gesture-handler';
import React from 'react';
import { Platform, TouchableOpacity, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from './src/screens/HomeScreen';
import CustomerScreen from './src/screens/CustomerScreen';
import ChatScreen from './src/screens/ChatScreen';

const Stack = createStackNavigator();

export default function App() {
    // Fix para Web: Garante que o corpo da página permita scroll e carrega fontes
    if (Platform.OS === 'web') {
        // Carrega fonte Montserrat
        const style = document.createElement('style');
        style.textContent = `
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');
            html, body, #root {
                height: 100%;
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
            }
        `;
        document.head.appendChild(style);

        // Carrega fonte Material Icons (necessário para @expo/vector-icons funcionar na web)
        const iconLink = document.createElement('link');
        iconLink.href = 'https://fonts.googleapis.com/icon?family=Material+Icons';
        iconLink.rel = 'stylesheet';
        document.head.appendChild(iconLink);
    }

    return (
        <NavigationContainer>
            <Stack.Navigator
                screenOptions={{
                    cardStyle: { flex: 1 },
                    headerStyle: {
                        backgroundColor: '#1A2F5A',
                        elevation: 0, // Remove shadow for cleaner look
                        shadowOpacity: 0,
                    },
                    headerTintColor: '#fff',
                    headerTitleStyle: {
                        fontWeight: 'bold',
                        fontFamily: Platform.OS === 'web' ? 'Montserrat' : undefined,
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
                            fontFamily: Platform.OS === 'web' ? 'Montserrat' : undefined,
                        },
                    }}
                />
                <Stack.Screen
                    name="Customer"
                    component={CustomerScreen}
                    options={({ navigation }) => ({
                        title: 'Detalhes do Cliente',
                        headerTitleAlign: 'center',
                        headerLeft: () => (
                            <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginLeft: 15 }}>
                                <Text style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>Voltar</Text>
                            </TouchableOpacity>
                        )
                    })}
                />
                <Stack.Screen
                    name="Chat"
                    component={ChatScreen}
                    options={({ navigation }) => ({
                        title: 'Chat com Mari IA',
                        headerTitleAlign: 'center',
                        headerLeft: () => (
                            <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginLeft: 15 }}>
                                <Text style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>Voltar</Text>
                            </TouchableOpacity>
                        )
                    })}
                />
            </Stack.Navigator>
        </NavigationContainer>
    );
}
