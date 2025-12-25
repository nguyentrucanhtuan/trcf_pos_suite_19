/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";

export class TrcfVatSendProgress extends Component {
    static template = "trcf_minvoice.TrcfVatSendProgress";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.resModel = this.props.record.resModel;
        this.resId = this.props.record.resId;

        this.state = useState({
            isProcessing: false,
            isDone: false,
            total: 0,
            success: 0,
            failed: 0,
            pending: 0,
            lines: [],
        });

        onWillStart(async () => {
            await this._loadWizardData();
        });
    }

    async _loadWizardData() {
        const data = await this.orm.read(this.resModel, [this.resId], [
            "total_count", "success_count", "failed_count", "pending_count", "line_ids", "state"
        ]);
        const wizard = data[0];
        this.state.total = wizard.total_count;
        this.state.success = wizard.success_count;
        this.state.failed = wizard.failed_count;
        this.state.pending = wizard.pending_count;
        this.state.isDone = wizard.state === "done";

        if (wizard.line_ids && wizard.line_ids.length > 0) {
            const lines = await this.orm.read("trcf.vat.send.wizard.line", wizard.line_ids, [
                "order_ref", "order_amount", "status", "vat_code", "error_message"
            ]);
            this.state.lines = lines;
        } else {
            this.state.lines = [];
        }
    }

    async startProcessing() {
        if (this.state.isProcessing) return;
        this.state.isProcessing = true;

        const pendingLines = this.state.lines.filter(l => l.status === 'pending');

        for (const line of pendingLines) {
            line.status = 'processing';
            try {
                const result = await this.orm.call(this.resModel, "action_rpc_process_line", [
                    [this.resId], line.id
                ]);

                line.status = result.status;
                line.vat_code = result.vat_code;
                line.error_message = result.error_message;

                this.state.success = result.counts.success;
                this.state.failed = result.counts.failed;
                this.state.pending = result.counts.pending;
                this.state.isDone = result.all_done;

            } catch (error) {
                line.status = 'failed';
                line.error_message = error.message || "Unknown error";
                this.state.failed++;
                this.state.pending--;
            }
        }

        this.state.isProcessing = false;
        if (this.state.isDone) {
            this.notification.add("Đã hoàn thành phát hành hóa đơn!", {
                type: "success",
            });
        }
    }
}

registry.category("view_widgets").add("trcf_vat_send_progress", {
    component: TrcfVatSendProgress,
});
