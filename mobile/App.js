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
    // Fix para Web: Garante que o corpo da página permita scroll e carrega fonte
    if (Platform.OS === 'web') {
        const style = document.createElement('style');
        style.textContent = `
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');
            html, body, #root {
                height: 100%;
                overflow: hidden;
            }
        `;
        document.head.appendChild(style);
    }

    return (
        <NavigationContainer>
            <Stack.Navigator
                screenOptions={{
                    cardStyle: { flex: 1 },
                    headerStyle: {
                        backgroundColor: '#6200ee',
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
                        headerTitleStyle: {
                            fontWeight: 'bold',
                            fontSize: 24,
                            fontFamily: Platform.OS === 'web' ? 'Montserrat' : undefined,
                        },
                    }}
                />
                <Stack.Screen
                    name="Customer"
                    component={CustomerScreen}
                    options={({ navigation }) => ({
                        title: 'Detalhes do Cliente',
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
                        title: 'Assistente Mari IA',
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
