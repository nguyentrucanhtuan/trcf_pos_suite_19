/** @odoo-module */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MomoPaymentTerminal extends PaymentInterface {
    setup() {
        super.setup();
        this.state = useState({
            showQR: false,
            paymentAmount: 0,
            paymentStatus: 'pending'
        });
    }

    async sendPaymentRequest(cid) {
        await super.sendPaymentRequest(cid);
        
        const line = this.getPendingPaymentLine();
        if (!line) {
            return false;
        }

        const paymentMethod = line.payment_method_id;
        this.state.paymentAmount = line.amount;
        this.state.showQR = true;
        
        // Simulate payment process
        this._showMomoPayment(line);
        
        return true;
    }

    async sendPaymentCancel(order, cid) {
        await super.sendPaymentCancel(order, cid);
        this.state.showQR = false;
        this.state.paymentStatus = 'cancelled';
        return true;
    }

    async sendPaymentReverse(cid) {
        await super.sendPaymentReverse(cid);
        this.state.showQR = false;
        return true;
    }

    _showMomoPayment(line) {
        const paymentMethod = line.payment_method_id;
        
        // Create popup to show QR code
        this.env.services.dialog.add(MomoPaymentDialog, {
            title: _t('MOMO Payment'),
            amount: line.amount,
            qrImage: paymentMethod.momo_qr_image,
            merchantId: paymentMethod.momo_merchant_id,
            phoneNumber: paymentMethod.momo_phone_number,
            onConfirm: () => {
                // Simulate successful payment
                line.setPaymentStatus('done');
                this.state.showQR = false;
                this.state.paymentStatus = 'done';
            },
            onCancel: () => {
                // Cancel payment
                line.setPaymentStatus('retry');
                this.state.showQR = false;
                this.state.paymentStatus = 'cancelled';
            }
        });
    }
}

// Dialog component to show MOMO QR
export class MomoPaymentDialog extends Component {
    static template = "momo_payment_terminal.MomoPaymentDialog";
    static props = {
        title: String,
        amount: Number,
        qrImage: { type: String, optional: true },
        merchantId: { type: String, optional: true },
        phoneNumber: { type: String, optional: true },
        onConfirm: Function,
        onCancel: Function,
        close: Function,
    };

    setup() {
        this.state = useState({
            waiting: true,
            countdown: 60, // 60 seconds timeout
        });
        
        onMounted(() => {
            this.startCountdown();
        });
    }

    startCountdown() {
        this.countdownInterval = setInterval(() => {
            this.state.countdown--;
            if (this.state.countdown <= 0) {
                clearInterval(this.countdownInterval);
                this.props.onCancel();
                this.props.close();
            }
        }, 1000);
    }

    confirmPayment() {
        clearInterval(this.countdownInterval);
        this.props.onConfirm();
        this.props.close();
    }

    cancelPayment() {
        clearInterval(this.countdownInterval);
        this.props.onCancel();
        this.props.close();
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    }
}

registry.category("payment_methods").add("momo", MomoPaymentTerminal);
