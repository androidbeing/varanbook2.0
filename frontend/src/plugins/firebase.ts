import { initializeApp } from 'firebase/app'
import { getAnalytics } from 'firebase/analytics'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: 'AIzaSyCKX0ntYgGp9dZYPw9dz9qFhkECud9CWew',
  authDomain: 'varanbook-bb907.firebaseapp.com',
  projectId: 'varanbook-bb907',
  storageBucket: 'varanbook-bb907.firebasestorage.app',
  messagingSenderId: '612615947132',
  appId: '1:612615947132:web:ee93f6150ec003e1e21af9',
  measurementId: 'G-3JY8TRQYHB',
}

export const firebaseApp = initializeApp(firebaseConfig)
export const analytics = getAnalytics(firebaseApp)
// Pre-initialise Auth so phone OTP is ready on first use
export const firebaseAuth = getAuth(firebaseApp)
