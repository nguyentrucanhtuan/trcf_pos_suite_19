/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component, useState, onWillStart, onMounted } = owl;
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { TrcfKitchenDashboard } from "./trcf_kitchen_dashboard";

export class TrcfUnifiedDashboard extends Component {
    static components = { TrcfKitchenDashboard };
    setup() {
        this.busService = this.env.services.bus_service;

        this.state = useState({
            activeTab: 'kitchen',
            hasNewOrder: false,
            showTaskPopup: false,
            upcomingTask: null,
            currentTime: new Date(),
        });

        // URLs cho iframes
        this.kitchenUrl = `/odoo/action-trcf_kitchen_screen.kitchen_dashboard_action`;
        // Lưu ý: Chúng ta sẽ dùng URL route trực tiếp để tránh vòng lặp nếu có thể,
        // nhưng kitchen dashboard hiện đang là client action phức tạp.
        // Để đơn giản và giữ logic, ta sẽ dùng iframe trỏ tới route controller nếu có, 
        // hoặc chính client action nhưng với tag khác.

        // Lấy screen_id từ context để biết đang hiển thị cho bếp nào
        this.screen_id = (this.props.action.context && this.props.action.context.active_id) || 1;

        // Sử dụng route trực tiếp thay vì client action để tránh lỗi X-Frame-Options
        this.kitchenIframeUrl = `/pos/kitchen_screen/${this.screen_id}`;
        this.tasksUrl = `/team-tasks?minimal=1`;

        this.busService.addChannel("pos_order_created");
        this._onBusMessage = this.onBusMessage.bind(this);

        onWillStart(() => {
            this.busService.subscribe('notification', this._onBusMessage);
        });

        onMounted(() => {
            this.updateClock();
            setInterval(() => this.updateClock(), 1000);
            setInterval(() => this.checkTasks(), 30000); // Mỗi 30s kiểm tra task
        });
    }

    updateClock() {
        this.state.currentTime = new Date();
    }

    onBusMessage(message) {
        if (message.message === "pos_order_created" && this.state.activeTab !== 'kitchen') {
            this.state.hasNewOrder = true;
            // Có thể phát thêm âm thanh ở đây
        }
    }

    async checkTasks() {
        // Mock logic kiểm tra task sắp tới (tương tự trcf_task_template.xml)
        // Trong thực tế, có thể gọi RPC để lấy danh sách task hiện tại
        try {
            const result = await rpc("/team-tasks/refresh", {});
            if (result && result.success && result.employees) {
                const now = new Date();
                const currentHour = now.getHours() + now.getMinutes() / 60;

                let foundUpcoming = false;
                result.employees.forEach(emp => {
                    emp.tasks.forEach(task => {
                        const diff = task.time_start - currentHour;
                        if (task.state === 'pending' && diff <= 5 / 60 && diff >= -1 / 60) {
                            if (!this.state.showTaskPopup && this.state.activeTab !== 'tasks') {
                                this.state.upcomingTask = task;
                                this.state.showTaskPopup = true;
                                foundUpcoming = true;
                            }
                        }
                    });
                });
            }
        } catch (e) {
            console.error("Lỗi kiểm tra task:", e);
        }
    }

    switchTab(tab) {
        this.state.activeTab = tab;
        if (tab === 'kitchen') {
            this.state.hasNewOrder = false;
        }
    }

    closeTaskPopup() {
        this.state.showTaskPopup = false;
    }

    goToTasks() {
        this.state.showTaskPopup = false;
        this.switchTab('tasks');
    }

    get upcomingTaskDescription() {
        return (this.state.upcomingTask && this.state.upcomingTask.description)
            || _t('Vui lòng thực hiện công việc đúng hạn.');
    }
}

TrcfUnifiedDashboard.template = "trcf_kitchen_screen.UnifiedDashboardTemplate";
registry.category("actions").add("trcf_unified_dashboard_tags", TrcfUnifiedDashboard);
