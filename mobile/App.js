import 'react-native-gesture-handler';
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from './src/screens/HomeScreen';
import CustomerScreen from './src/screens/CustomerScreen';
import ChatScreen from './src/screens/ChatScreen';

const Stack = createStackNavigator();

export default function App() {
    return (
        <NavigationContainer>
            <Stack.Navigator>
                <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'MariIA Telesales' }} />
                <Stack.Screen name="Customer" component={CustomerScreen} options={{ title: 'Detalhes do Cliente' }} />
                <Stack.Screen name="Chat" component={ChatScreen} options={{ title: 'Assistente MariIA' }} />
            </Stack.Navigator>
        </NavigationContainer>
    );
}
