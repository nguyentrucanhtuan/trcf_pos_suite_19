/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";

class TrcfShiftScheduleGrid extends Component {
    static template = xml`
        <div class="o_action h-100">
            <iframe src="/shift-schedule" 
                    style="width: 100%; height: 100%; border: none;"/>
        </div>
    `;
}

// Register the client action
registry.category("actions").add("trcf_shift_schedule_grid_action", TrcfShiftScheduleGrid);
