/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { registry } from "@web/core/registry";

export class PaymentMoMo extends PaymentInterface {
    setup() {
        super.setup();
    }
   
}

// Đăng ký terminal
registry.category("payment_terminals").add("trcf_momo_terminal", PaymentMoMo);