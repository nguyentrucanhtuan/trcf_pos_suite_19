/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

// Patch PosStore to include MOMO payment fields
patch(PosStore.prototype, {
    async _loadPosPaymentMethods(payment_methods) {
        await super._loadPosPaymentMethods(...arguments);
        
        // Add MOMO specific fields to payment methods
        for (const pm of payment_methods) {
            if (pm.use_payment_terminal === 'momo') {
                // These fields are loaded from the backend
                pm.momo_merchant_id = pm.momo_merchant_id || '';
                pm.momo_qr_image = pm.momo_qr_image || '';
                pm.momo_phone_number = pm.momo_phone_number || '';
            }
        }
    }
});
