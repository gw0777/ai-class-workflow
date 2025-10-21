/**
 * Cloud Functions Entry Point
 * AI Resume Master - Payment System
 */

import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';

// Firebase Admin 초기화
admin.initializeApp();

// Payment Functions
export { confirmTossPayment } from './payment/confirmPayment';
export { handlePaymentWebhook } from './payment/webhook';
export { refundPayment } from './payment/refund';

// Subscription Functions
export { checkExpiredSubscriptions } from './subscription/checkExpired';
export { renewSubscription } from './subscription/renew';
