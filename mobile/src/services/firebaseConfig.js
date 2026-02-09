import { initializeApp } from 'firebase/app';
import {
    initializeAuth,
    getReactNativePersistence,
    browserLocalPersistence
} from 'firebase/auth';
import { initializeFirestore } from 'firebase/firestore';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

const firebaseConfig = {
    apiKey: "AIzaSyBv05Nvqdpk5wzbRgFK2hjIEkpr8cGa6t4",
    authDomain: "amazing-firefly-475113-p3.firebaseapp.com",
    projectId: "amazing-firefly-475113-p3",
    storageBucket: "amazing-firefly-475113-p3.firebasestorage.app",
    messagingSenderId: "635293407607",
    appId: "1:635293407607:web:2d10c573f1bf0c27d6a972"
};

const app = initializeApp(firebaseConfig);
console.log("[DEBUG] Firebase Initialized. Project ID:", firebaseConfig.projectId);

let auth;

if (Platform.OS === 'web') {
    // Web: Use browserLocalPersistence
    auth = initializeAuth(app, {
        persistence: browserLocalPersistence
    });
} else {
    // Native: Use AsyncStorage
    auth = initializeAuth(app, {
        persistence: getReactNativePersistence(AsyncStorage)
    });
}

// 🌐 Robust Firestore Initialization
// Enabling 'experimentalForceLongPolling' and disabling 'useFetchStreams' 
// helps in corporate networks where standard gRPC/WebSockets/Streams are blocked.
const db = initializeFirestore(app, {
    experimentalForceLongPolling: true,
    useFetchStreams: false,
});

export { auth, db };
