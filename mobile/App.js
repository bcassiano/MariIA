import 'react-native-gesture-handler';
import React from 'react';
import { Platform } from 'react-native';
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
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
            }
        `;
        document.head.appendChild(style);
    }

    return (
        <NavigationContainer>
            <Stack.Navigator
                screenOptions={{
                    cardStyle: { flex: 1 } // Garante que as telas ocupem todo o espaço
                }}
            >
                <Stack.Screen
                    name="Home"
                    component={HomeScreen}
                    options={{
                        title: 'Mari IA',
                        headerStyle: {
                            backgroundColor: '#6200ee',
                        },
                        headerTintColor: '#fff',
                        headerTitleStyle: {
                            fontWeight: 'bold',
                            fontSize: 24,
                            fontFamily: 'Montserrat',
                        },
                    }}
                />
                <Stack.Screen name="Customer" component={CustomerScreen} options={{ title: 'Detalhes do Cliente' }} />
                <Stack.Screen name="Chat" component={ChatScreen} options={{ title: 'Assistente Mari IA' }} />
            </Stack.Navigator>
        </NavigationContainer>
    );
}
