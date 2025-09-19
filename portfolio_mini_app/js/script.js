import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import { getFirestore, addDoc, collection } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

// --- Глобальные переменные ---
let db;
const tg = window.Telegram.WebApp;
const appId = typeof __app_id !== 'undefined' ? __app_id : 'portfolio-v0';

// --- Инициализация ---
initialize();

function initialize() {
    // Настраиваем приложение Telegram
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#000000');
    tg.setBackgroundColor('#000000');

    // Инициализируем Firebase
    try {
        const firebaseConfig = {
            apiKey: "AIzaSyDYdFiLUAooCRXryegS_3kB_LHC8d1_Icg",
            authDomain: "portfolio-v0-482bc.firebaseapp.com",
            projectId: "portfolio-v0-482bc",
            storageBucket: "portfolio-v0-482bc.firebasestorage.app",
            messagingSenderId: "1000303794889",
            appId: "1:1000303794889:web:ef6866fbf08163a9a8cb18",
            measurementId: "G-90GY3HXZ7K"
        };
        if (!firebaseConfig.apiKey) {
            console.error("Firebase config is missing.");
            return;
        }
        const app = initializeApp(firebaseConfig);
        db = getFirestore(app);
        console.log("✅ Firebase initialized successfully!");

        // Отслеживаем первый заход на страницу, если это главная
        if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/')) {
             trackEvent('page_view_main');
        }

    } catch (e) {
        console.error("Error initializing Firebase:", e);
    }
}

/**
 * Отправляет событие в Firestore для аналитики.
 * @param {string} eventName - Название события.
 * @param {object} eventData - Дополнительные данные.
 */
export function trackEvent(eventName, eventData = {}) {

    return;

    if (!db) {
        console.warn(`Firebase not initialized. Mock event: '${eventName}'`, eventData);
        return;
    }

    const userId = tg.initDataUnsafe?.user?.id || 'unknown_user';
    const platform = tg.platform || 'unknown';

    try {
        const eventCollectionRef = collection(db, `artifacts/${appId}/public/data/events`);
        addDoc(eventCollectionRef, {
            userId: String(userId),
            eventName: eventName,
            eventData: eventData,
            timestamp: new Date(),
            platform: platform,
            url: window.location.pathname,
        }).then(docRef => {
            console.log(`Event '${eventName}' tracked with ID: ${docRef.id}`);
        });
    } catch (error) {
        console.error("Error tracking event: ", error);
    }
}

