import {
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signOut,
    onAuthStateChanged,
    sendEmailVerification
} from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { auth, db } from './firebaseConfig';
import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Service to handle Authentication logic centrally.
 */
export const AuthService = {
    /**
     * Observable for Auth State changes.
     * @param {function} callback - Function(user|null)
     * @returns {function} Unsubscribe function
     */
    onAuthStateChanged: (callback) => {
        return onAuthStateChanged(auth, callback);
    },

    auth: auth, // Expose for debugging

    getCurrentUser: () => {
        return auth.currentUser;
    },

    /**
     * Login with Email/Password
     * @param {string} email 
     * @param {string} password 
     * @returns {Promise<object>} User object with slpCode
     */
    login: async (email, password) => {
        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            let user = userCredential.user;
            console.log(`[DEBUG Auth] Login. UID: ${user.uid}, Verified (pre-reload): ${user.emailVerified}`);

            // Force reload to ensure 'emailVerified' is up to date
            await user.reload();

            // 🔑 Critical: Force a new ID token from the server to get fresh claims
            await user.getIdToken(true);

            // Refetch the user object after token refresh
            user = auth.currentUser;
            console.log(`[DEBUG Auth] Login. Verified (post-reload+token): ${user?.emailVerified}`);

            if (!user.emailVerified) {
                console.log("[DEBUG Auth] Email still not verified. Signing out.");
                await signOut(auth);
                throw new Error("E-mail não verificado. Verifique sua caixa de entrada.");
            }

            // Fetch SAP Link
            const slpCode = await AuthService.getSapId(user.uid);

            return { ...user, slpCode };
        } catch (error) {
            throw error;
        }
    },

    /**
     * Register new user and link to SAP SlpCode
     * @param {string} email 
     * @param {string} password 
     * @param {string} slpCode - SAP Sales Person Code
     */
    register: async (email, password, slpCode) => {
        try {
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;

            // Send Verification Email
            await sendEmailVerification(user);

            // Save Link to Firestore: users/{uid} -> { slpCode: ... }
            await setDoc(doc(db, "users", user.uid), {
                email: email,
                slpCode: slpCode,
                createdAt: new Date().toISOString()
            });

            // Force logout so user has to verify email
            await signOut(auth);

            return user;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Logout
     */
    logout: async () => {
        await AsyncStorage.removeItem('user_session_id');
        await AsyncStorage.removeItem('auth_strategy');
        return signOut(auth);
    },

    /**
     * Helper: Get SAP ID from Firestore by UID
     */
    async getSapId(uid) {
        try {
            console.log(`[DEBUG Auth] Fetching SAP ID for UID: ${uid}...`);
            const docRef = doc(db, "users", uid);
            const docSnap = await getDoc(docRef);

            if (docSnap.exists()) {
                const slpCode = docSnap.data().slpCode;
                console.log(`[DEBUG Auth] Success! SAP ID: ${slpCode}`);
                return slpCode;
            }
            console.warn(`[DEBUG Auth] No document found for UID: ${uid}`);
            return null;
        } catch (error) {
            console.error("Error fetching SAP ID:", error);
            if (error.code === 'unavailable' || error.message.includes('offline')) {
                console.error("CRITICAL: Firestore is unreachable. Your network/firewall might be blocking it.");
            }
            throw error;
        }
    }
};
