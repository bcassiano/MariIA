import 'react-native-gesture-handler';
import React from 'react';
import { Platform, View, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import * as Font from 'expo-font';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Linking from 'expo-linking';
import tw from 'twrnc';

// Screens
import HomeScreen from './src/screens/HomeScreen';
import CustomerScreen from './src/screens/CustomerScreen';
import ChatScreen from './src/screens/ChatScreen';
import PortfolioScreen from './src/screens/PortfolioScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';

// Components & Services
import Icon from './src/components/Icon';
import { AuthService } from './src/services/auth';
import { SapService } from './src/services/sapService';
import Toast from './src/components/Toast';

const Stack = createStackNavigator();
const AuthStack = createStackNavigator();

function AppStackScreen() {
    return (
        <Stack.Navigator
            screenOptions={{
                cardStyle: { flex: 1 },
                headerStyle: {
                    backgroundColor: '#1A2F5A',
                    elevation: 0,
                },
                headerTintColor: '#fff',
                headerBackTitleVisible: false,
                headerBackImage: () => <Icon name="chevron_left" size={28} color="#fff" style={{ marginLeft: 10 }} />,
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
    );
}

function AuthStackScreen() {
    return (
        <AuthStack.Navigator screenOptions={{ headerShown: false }}>
            <AuthStack.Screen name="Login" component={LoginScreen} />
            <AuthStack.Screen name="Register" component={RegisterScreen} />
        </AuthStack.Navigator>
    );
}

export default function App() {
    const [fontsLoaded, setFontsLoaded] = React.useState(false);
    const [isAuthenticated, setIsAuthenticated] = React.useState(false);
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
        async function loadResourcesAndSession() {
            try {
                // 1. Check URL Param (Priority 1) - BYPASS STRATEGY
                let urlUserId = null;
                if (Platform.OS === 'web') {
                    const params = new URLSearchParams(window.location.search);
                    urlUserId = params.get('user_id');
                } else {
                    const initialUrl = await Linking.getInitialURL();
                    if (initialUrl) {
                        const { queryParams } = Linking.parse(initialUrl);
                        urlUserId = queryParams?.user_id;
                    }
                }

                if (urlUserId) {
                    console.log("Smart Login: URL Param detected =", urlUserId);
                    await AsyncStorage.setItem('user_session_id', urlUserId);
                    await AsyncStorage.setItem('auth_strategy', 'url_bypass'); // Mark as bypass
                    setIsAuthenticated(true);
                    return; // Done
                }

                // 2. Check Async Storage (Persistence) (Priority 2)
                const storedUserId = await AsyncStorage.getItem('user_session_id');
                const authStrategy = await AsyncStorage.getItem('auth_strategy');

                // SECURITY: Only trust storage blindly if it is a 'url_bypass' session.
                // If it is 'firebase' (or null/legacy), we MUST wait for onAuthStateChanged.
                if (storedUserId && authStrategy === 'url_bypass') {
                    console.log("Smart Login: Stored Session (Bypass) detected =", storedUserId);
                    setIsAuthenticated(true);
                    return;
                }

                // If we are here, we wait for Firebase. Do NOT set isAuthenticated(true).

            } catch (e) {
                console.warn("Error initializing app", e);
            } finally {
                setFontsLoaded(true);
                // Don't set isLoading(false) here, wait for Auth
            }
        }

        loadResourcesAndSession();

        // Firebase Listener
        const unsubscribe = AuthService.onAuthStateChanged(async (user) => {
            if (user) {
                // 🔐 ADMIN BYPASS: Masquerade as Renata Rodrigues
                // This allows the admin/developer to test the app with full data access
                if (user.email === 'bruno.cassiano@fantasticoalimentos.com.br') {
                    console.log("🔐 ADMIN BYPASS DETECTED: Activating Renata Mode");
                    await AsyncStorage.setItem('user_session_id', 'V.vp - Renata Rodrigues');
                    await AsyncStorage.setItem('auth_strategy', 'firebase');
                    await AsyncStorage.setItem('user_status', 'active');
                    setIsAuthenticated(true);
                    setIsLoading(false);
                    return;
                }

                // 🔄 Critical Fix: Force reload to ensure 'emailVerified' is fresh!
                try {
                    // Safe access to projectId to prevent crashes
                    const projectId = AuthService.auth?.app?.options?.projectId || "amazing-firefly-475113-p3";
                    console.log(`[DEBUG App.js] Auth State Changed. Project: ${projectId}, UID: ${user.uid}, Pre-reload Verified: ${user.emailVerified}`);
                    await user.reload();

                    // 🔑 Critical: Force a new ID token from the server to get fresh claims
                    await user.getIdToken(true);

                    // Refetch user after token refresh
                    const freshUser = AuthService.getCurrentUser();
                    if (freshUser) {
                        user = freshUser;
                    }
                    console.log(`[DEBUG App.js] Post-reload+token Verified: ${user.emailVerified}`);

                } catch (e) {
                    console.log("Failed to reload user in App.js (Possible Account Deletion):", e);
                    // SECURITY: If reload fails (e.g. user deleted), Log Out immediately.
                    if (e.code === 'auth/user-not-found' || e.code === 'auth/user-token-expired') {
                        console.warn("Security: User not found or token expired. Forcing Logout.");
                        await AuthService.logout();
                        setIsAuthenticated(false);
                        setIsLoading(false);
                        return;
                    }
                }

                // Only allow access if user exists AND email is verified
                if (user.emailVerified) {
                    console.log("Smart Login: Firebase User detected (Verified) =", user.uid);
                    // Fetch the linked SAP ID
                    try {
                        try {
                            // Race condition: Firestore fetch vs 3s timeout
                            const firestorePromise = AuthService.getSapId(user.uid);
                            const timeoutPromise = new Promise((_, reject) =>
                                setTimeout(() => reject(new Error("Firestore timeout")), 3000)
                            );

                            slpCode = await Promise.race([firestorePromise, timeoutPromise]);
                            console.log(`[DEBUG App.js] Firestore SAP ID for ${user.uid}:`, slpCode);
                        } catch (firestoreErr) {
                            console.warn("[DEBUG App.js] Firestore unavailable/slow. Using SapService fallback.", firestoreErr.message);
                            slpCode = await SapService.getSlpCodeByEmail(user.email);
                        }

                        if (!slpCode) {
                            console.log("[DEBUG App.js] Firestore returned null. Trying SapService fallback...");
                            slpCode = await SapService.getSlpCodeByEmail(user.email);
                        }

                        if (slpCode) {
                            await AsyncStorage.setItem('user_session_id', slpCode.toString());
                            await AsyncStorage.setItem('auth_strategy', 'firebase'); // Mark as secure session
                            await AsyncStorage.setItem('user_status', 'active');
                            setIsAuthenticated(true);
                        } else {
                            console.warn("Smart Login: User has no SAP Code. Activating PENDING mode.");
                            // Allow login but marked as pending
                            await AsyncStorage.setItem('user_status', 'pending');
                            await AsyncStorage.setItem('auth_strategy', 'firebase');
                            // Clear potential stale session ID
                            await AsyncStorage.removeItem('user_session_id');
                            setIsAuthenticated(true);
                        }
                    } catch (err) {
                        console.error("Smart Login Error (UID/Email mapping failed):", err);
                        // Even on error, if we have a user, let them in as Pending to avoid lockout
                        await AsyncStorage.setItem('user_status', 'pending');
                        setIsAuthenticated(true);
                    }
                } else {
                    console.log("Smart Login: User detected but Email NOT Verified. Access Denied.");
                    // ⛔ Access Denied: User must be verified.
                    await AuthService.logout();
                    setIsAuthenticated(false);
                }
            } else {
                // User is null (No Firebase Session)

                // Check if we are allowed to stay logged in (URL Bypass)
                const authStrategy = await AsyncStorage.getItem('auth_strategy');

                if (authStrategy !== 'url_bypass') {
                    // If it's not a bypass session, and Firebase says "no user", then we are OUT.
                    console.log("Smart Login: No Firebase User and no Bypass Strategy. Logging out.");
                    setIsAuthenticated(false);
                    // Ensure stale data is gone
                    if (await AsyncStorage.getItem('user_session_id')) {
                        await AsyncStorage.removeItem('user_session_id');
                        await AsyncStorage.removeItem('auth_strategy');
                    }
                }
            }
            setIsLoading(false);
        });

        return () => unsubscribe();
    }, []);

    if (isLoading || !fontsLoaded) {
        return (
            <View style={tw`flex-1 justify-center items-center bg-white`}>
                <ActivityIndicator size="large" color="#1A2F5A" />
            </View>
        );
    }

    return (
        <SafeAreaProvider>
            <NavigationContainer>
                {isAuthenticated ? <AppStackScreen /> : <AuthStackScreen />}
            </NavigationContainer>
            <Toast />
        </SafeAreaProvider>
    );
}
