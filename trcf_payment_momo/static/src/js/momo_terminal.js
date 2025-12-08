/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useState } from "@odoo/owl";

// Default MoMo QR placeholder SVG
const DEFAULT_MOMO_QR_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect fill="#fff" width="200" height="200" rx="10"/>
  <rect fill="#a50064" x="10" y="10" width="180" height="180" rx="8"/>
  <text x="100" y="85" text-anchor="middle" font-size="22" fill="#fff" font-family="Arial, sans-serif" font-weight="bold">MoMo</text>
  <text x="100" y="110" text-anchor="middle" font-size="12" fill="#fff" font-family="Arial, sans-serif">Scan to pay</text>
  <text x="100" y="130" text-anchor="middle" font-size="10" fill="#ffcce6" font-family="Arial, sans-serif">Upload QR in Settings</text>
</svg>`;

const DEFAULT_MOMO_QR = "data:image/svg+xml," + encodeURIComponent(DEFAULT_MOMO_QR_SVG.trim());

/**
 * TRCF MoMo Payment Terminal
 */
export class TrcfMomoPaymentTerminal extends PaymentInterface {

    get fastPayments() {
        return false;
    }

    _getQRCodeUrl() {
        const qrBase64 = this.payment_method_id.momo_qr_code;
        if (qrBase64) {
            return `data:image/png;base64,${qrBase64}`;
        }
        return DEFAULT_MOMO_QR;
    }

    async sendPaymentRequest(uuid) {
        await super.sendPaymentRequest(uuid);

        if (!this.pos) {
            return false;
        }

        const line = this.pos.getOrder()?.getSelectedPaymentline();
        if (!line) {
            return false;
        }

        // Set payment as done immediately (manual confirmation)
        line.setPaymentStatus('done');

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

// Register terminal
register_payment_method("trcf_momo", TrcfMomoPaymentTerminal);

// Patch PaymentScreen to show QR
patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.momoState = useState({
            showQr: false,
            qrCode: DEFAULT_MOMO_QR,
        });
    },

    addNewPaymentLine(paymentMethod) {
        const result = super.addNewPaymentLine(...arguments);

        if (paymentMethod.use_payment_terminal === 'trcf_momo') {
            const qrBase64 = paymentMethod.momo_qr_code;
            if (qrBase64) {
                this.momoState.qrCode = `data:image/png;base64,${qrBase64}`;
            } else {
                this.momoState.qrCode = DEFAULT_MOMO_QR;
            }
            this.momoState.showQr = true;
        } else {
            this.momoState.showQr = false;
        }

        return result;
    },

    deletePaymentLine(uuid) {
        const line = this.paymentLines.find((l) => l.uuid === uuid);
        if (line?.payment_method_id?.use_payment_terminal === 'trcf_momo') {
            this.momoState.showQr = false;
        }
        return super.deletePaymentLine(...arguments);
    },

    get momoQrCode() {
        return this.momoState.qrCode;
    },

    get showMomoQr() {
        return this.paymentLines.some(
            line => line.payment_method_id?.use_payment_terminal === 'trcf_momo'
        );
    }
});