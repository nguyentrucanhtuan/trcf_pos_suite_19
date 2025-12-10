/** @odoo-module **/
/**
 * MoMo Payment Terminal Integration for Odoo 19 POS
 * 
 * This module provides:
 * 1. Dynamic QR code generation via MoMo API
 * 2. Real-time payment confirmation via webhook + Odoo bus
 * 3. Automatic order validation after successful payment
 * 
 * Flow:
 * - User selects MoMo payment → API creates payment request → QR displayed
 * - Customer scans QR with MoMo app → Pays → MoMo calls webhook
 * - Webhook updates transaction → Sends bus notification → POS receives
 * - Payment marked done → Order auto-validated → Receipt printed
 */

import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useState, onWillUnmount } from "@odoo/owl";
import { getOnNotified } from "@point_of_sale/utils";

// ============================================================================
// Constants: QR Code Placeholder SVGs
// ============================================================================

/** Default placeholder when no QR is available */
const DEFAULT_MOMO_QR_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect fill="#fff" width="200" height="200" rx="10"/>
  <rect fill="#a50064" x="10" y="10" width="180" height="180" rx="8"/>
  <text x="100" y="85" text-anchor="middle" font-size="22" fill="#fff" font-family="Arial, sans-serif" font-weight="bold">MoMo</text>
  <text x="100" y="110" text-anchor="middle" font-size="12" fill="#fff" font-family="Arial, sans-serif">Scan QR</text>
  <text x="100" y="130" text-anchor="middle" font-size="10" fill="#ffcce6" font-family="Arial, sans-serif">Upload QR in Settings</text>
</svg>`;
const DEFAULT_MOMO_QR = "data:image/svg+xml," + encodeURIComponent(DEFAULT_MOMO_QR_SVG.trim());

/** Loading spinner while MoMo API is being called */
const LOADING_QR_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect fill="#fff" width="200" height="200" rx="10"/>
  <rect fill="#a50064" x="10" y="10" width="180" height="180" rx="8"/>
  <text x="100" y="100" text-anchor="middle" font-size="16" fill="#fff" font-family="Arial, sans-serif">Dang tao QR...</text>
</svg>`;
const LOADING_QR = "data:image/svg+xml," + encodeURIComponent(LOADING_QR_SVG.trim());

/** Success checkmark after payment confirmed */
const SUCCESS_QR_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect fill="#fff" width="200" height="200" rx="10"/>
  <rect fill="#28a745" x="10" y="10" width="180" height="180" rx="8"/>
  <text x="100" y="90" text-anchor="middle" font-size="48" fill="#fff" font-family="Arial">✓</text>
  <text x="100" y="130" text-anchor="middle" font-size="16" fill="#fff" font-family="Arial">Thanh cong!</text>
</svg>`;
const SUCCESS_QR = "data:image/svg+xml," + encodeURIComponent(SUCCESS_QR_SVG.trim());

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generate QR code image URL using quickchart.io API
 * @param {string} data - The data to encode in QR (MoMo deeplink URL)
 * @returns {string} URL to QR code image
 */
function generateQRCodeUrl(data) {
    return `https://quickchart.io/qr?text=${encodeURIComponent(data)}&size=200`;
}

// ============================================================================
// Payment Terminal Class
// ============================================================================

/**
 * MoMo Payment Terminal
 * Extends Odoo's PaymentInterface in wait for webhook confirmation
 */
export class TrcfMomoPaymentTerminal extends PaymentInterface {

    /** Disable fast payments - we wait for webhook confirmation */
    get fastPayments() {
        return false;
    }

    /**
     * Called when user clicks "Send" on payment line
     * Sets status to 'waiting' until webhook confirms payment
     */
    async sendPaymentRequest(uuid) {
        await super.sendPaymentRequest(uuid);
        if (!this.pos) return false;

        const line = this.pos.getOrder()?.getSelectedPaymentline();
        if (!line) return false;

        line.setPaymentStatus('waiting');
        return true;
    }

    sendPaymentCancel(order, uuid) {
        super.sendPaymentCancel(order, uuid);
        return Promise.resolve(true);
    }

    sendPaymentReversal(uuid) {
        super.sendPaymentReversal(uuid);
        return Promise.resolve(true);
    }
}

// Register terminal with Odoo POS
register_payment_method("trcf_momo", TrcfMomoPaymentTerminal);

// ============================================================================
// PaymentScreen Patch
// ============================================================================

/**
 * Extends PaymentScreen to:
 * 1. Display MoMo QR code when payment method selected
 * 2. Listen for webhook notifications via Odoo bus
 * 3. Auto-validate order on successful payment
 */
patch(PaymentScreen.prototype, {

    setup() {
        super.setup(...arguments);

        // Reactive state for QR display
        this.momoState = useState({
            showQr: false,
            qrCode: DEFAULT_MOMO_QR,
            loading: false,
            pendingOrderId: null,
        });

        // Subscribe to webhook notifications
        this._setupMomoPaymentListener();

        onWillUnmount(() => {
            this._cleanupMomoPaymentListener();
        });
    },

    /**
     * Subscribe to Odoo bus for MoMo payment success notifications
     * Uses Odoo 19 pattern: getOnNotified with config.access_token channel
     */
    _setupMomoPaymentListener() {
        const busService = this.env.services.bus_service;
        const accessToken = this.pos.config?.access_token;

        if (busService && accessToken) {
            const onNotified = getOnNotified(busService, accessToken);
            this._momoUnsubscribe = onNotified('MOMO_PAYMENT_SUCCESS', (payload) => {
                this._handleMomoPaymentSuccess(payload);
            });
        }
    },

    _cleanupMomoPaymentListener() {
        // Cleanup handled by OWL lifecycle
    },

    /**
     * Handle successful payment notification from webhook
     * - Marks payment line as done
     * - Shows success QR
     * - Auto-validates order
     * 
     * @param {Object} data - Payment data from webhook
     * @param {string} data.pos_order_ref - POS order reference
     * @param {string} data.momo_order_id - MoMo transaction ID
     * @param {number} data.amount - Payment amount
     */
    _handleMomoPaymentSuccess(data) {
        // Guard: ensure we have an active order with payment lines
        if (!this.currentOrder || !this.currentOrder.payment_ids) {
            return;
        }

        // Find MoMo payment line
        const momoLine = this.paymentLines.find(
            line => line.payment_method_id?.use_payment_terminal === 'trcf_momo'
        );

        if (momoLine) {
            // Mark payment as completed
            momoLine.setPaymentStatus('done');

            // Update QR to show success
            this.momoState.qrCode = SUCCESS_QR;

            // Auto-validate order (triggers receipt printing via trcf_printer_manager)
            setTimeout(() => {
                try {
                    const currentOrder = this.currentOrder;
                    if (currentOrder && currentOrder.isPaid() && !currentOrder.isRefundInProcess()) {
                        this.validateOrder(false);
                    }
                } catch (e) {
                    // Validation error - user can manually validate
                }
            }, 100);
        }
    },

    /**
     * Override to handle MoMo payment method selection
     * Calls MoMo API to create payment and get QR code
     */
    async addNewPaymentLine(paymentMethod) {
        const result = super.addNewPaymentLine(...arguments);

        if (paymentMethod.use_payment_terminal === 'trcf_momo') {
            this.momoState.showQr = true;
            this.momoState.loading = true;
            this.momoState.qrCode = LOADING_QR;

            // Prepare order data for MoMo API
            const order = this.currentOrder;
            let orderId = order.tracking_number || order.sequence_number || order.name;
            if (!orderId || orderId === '/' || orderId === 'Order') {
                orderId = (order.uid || '').split('-').pop() || `${Date.now()}`;
            }
            const amount = Math.round(order.getTotalDue());
            const orderInfo = `CFT${orderId}`;
            this.momoState.pendingOrderId = orderId;

            try {
                // Call backend RPC to create MoMo payment
                const response = await this.pos.data.call(
                    "pos.payment.method",
                    "create_momo_payment_rpc",
                    [],
                    {
                        order_id: orderId,
                        amount: amount,
                        order_info: orderInfo,
                        session_id: this.pos.session?.id,
                        config_id: this.pos.config?.id
                    }
                );

                if (response && response.success && response.qr_code_url) {
                    // Generate QR from MoMo deeplink URL
                    this.momoState.qrCode = generateQRCodeUrl(response.qr_code_url);
                } else {
                    // Fallback to static QR if available
                    this.momoState.qrCode = paymentMethod.momo_qr_code
                        ? `data:image/png;base64,${paymentMethod.momo_qr_code}`
                        : DEFAULT_MOMO_QR;
                }
            } catch (error) {
                // API error - use fallback QR
                this.momoState.qrCode = paymentMethod.momo_qr_code
                    ? `data:image/png;base64,${paymentMethod.momo_qr_code}`
                    : DEFAULT_MOMO_QR;
            } finally {
                this.momoState.loading = false;
            }
        } else {
            this.momoState.showQr = false;
        }

        return result;
    },

    /**
     * Override to hide QR when MoMo payment line is deleted
     */
    deletePaymentLine(uuid) {
        const line = this.paymentLines.find((l) => l.uuid === uuid);
        if (line?.payment_method_id?.use_payment_terminal === 'trcf_momo') {
            this.momoState.showQr = false;
            this.momoState.qrCode = DEFAULT_MOMO_QR;
            this.momoState.pendingOrderId = null;
        }
        return super.deletePaymentLine(...arguments);
    },

    // ========================================================================
    // Template Getters - Used by momo_payment_screen.xml template
    // ========================================================================

    /** Current QR code to display */
    get momoQrCode() {
        return this.momoState.qrCode;
    },

    /** Whether to show QR code section */
    get showMomoQr() {
        return this.paymentLines.some(
            line => line.payment_method_id?.use_payment_terminal === 'trcf_momo'
        );
    },

    /** Whether QR is loading */
    get momoLoading() {
        return this.momoState.loading;
    }
});