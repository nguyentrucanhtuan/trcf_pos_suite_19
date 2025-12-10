/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component, onWillStart, useState, onMounted } = owl;
import { useService } from "@web/core/utils/hooks";

export class TrcfKitchenDashboard extends Component {
    setup(env) {

        super.setup();
        this.busService = this.env.services.bus_service;

        // ✅ LẤY SCREEN ID TỪ URL odoo/action-xxx/SCREEN_ID/action-yyy
        this.screen_id = this.getScreenIdFromURL();

        // THÊM CHANNEL
        this.busService.addChannel("pos_order_created");
        this.busService.addChannel("pos_order_status_updated");
        this.busService.addChannel("pos_order_line_status_updated");

        this._onBusMessage = this.onBusMessage.bind(this);

        onWillStart(() => {
            this.busService.subscribe('notification', this._onBusMessage);
        })

        this.orm = useService("orm");
        var self = this
        // config_id sẽ được lấy từ screen_info sau khi load data
        self.config_id = null;

        this.state = useState({
            order_details: [],
            order_lines: [],
            config_id: null,
            stages: 'draft',
            draft_count: 0,
            waiting_count: 0,
            ready_count: 0,
            loadingOrders: [],
        });

        self.setupAudio();

        self.loadOrderData();
        self.loadOrderData_test();
    }

    // SETUP AUDIO VỚI FILE
    setupAudio() {
        try {
            // Thay 'your_module_name' bằng tên module thực tế của bạn
            this.notificationSound = new Audio('/trcf_kitchen_screen/static/src/sounds/notification.mp3');

            // Cài đặt âm lượng (0.0 - 1.0)
            this.notificationSound.volume = 1;

            // Preload để phát nhanh hơn
            this.notificationSound.preload = 'auto';

            // Xử lý lỗi nếu không load được file
            this.notificationSound.onerror = (error) => {
                console.warn('Không thể load file âm thanh:', error);
                this.notificationSound = null;
            };

            // Log khi load thành công
            this.notificationSound.oncanplaythrough = () => {
                console.log('File âm thanh đã sẵn sàng');
            };

        } catch (error) {
            console.warn('Lỗi khởi tạo audio:', error);
            this.notificationSound = null;
        }
    }

    // PHÁT ÂM THANH TỪ FILE
    playNotificationSound() {
        // Kiểm tra audio đã được khởi tạo chưa
        if (!this.notificationSound) {
            console.warn('Audio chưa được khởi tạo');
            return;
        }

        try {
            // Reset về đầu nếu đang phát
            this.notificationSound.currentTime = 0;

            // Phát âm thanh
            const playPromise = this.notificationSound.play();

            // Xử lý Promise (bắt buộc với một số trình duyệt)
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('Âm thanh đã phát thành công');
                    })
                    .catch(error => {
                        console.warn('Không thể phát âm thanh:', error);
                    });
            }
        } catch (error) {
            console.warn('Lỗi khi phát âm thanh:', error);
        }
    }

    onBusMessage(message) {
        var self = this

        // SỬ LÝ ĐƠN MỚI
        if (message.message === "pos_order_created"
            && message.res_model === "pos.order"
            && message.config_id) {

            console.log("đã nhận được thông tin", message);

            // PHÁT ÂM THANH THÔNG BÁO
            self.playNotificationSound();

            // LOAD LẠI DỮ LIỆU ĐƠN HÀNG
            self.loadOrderData();

            return;
        }


        // Xử lý cập nhật trạng thái đơn hàng
        if (message.message === "pos_order_status_updated" &&
            message.res_model === "pos.order" &&
            message.config_id == self.config_id) {

            console.log("🔄 Kitchen cập nhật trạng thái!", message);
            console.log(`📋 ${message.order_name}: ${message.old_status} → ${message.new_status}`);

            // Tự động cập nhật UI
            self.loadOrderData();

            // Dọn dẹp loading state
            const loadingIndex = self.state.loadingOrders.indexOf(message.order_id);
            if (loadingIndex > -1) {
                self.state.loadingOrders.splice(loadingIndex, 1);
                console.log(`🧹 Xóa loading state cho order ${message.order_id}`);
            }

            return; // Thoát sớm
        }

        //Sử lý cập nhật trạng thái món
        if (message.message === "pos_order_line_status_updated" &&
            message.res_model === "pos.order.line") {

            // LOAD LẠI DỮ LIỆU ĐƠN HÀNG
            self.loadOrderData();
            console.log("🔄 Kitchen cập nhật trạng thái món!", message);

            return;
        }
    }

    async loadOrderData_test() {
        var self = this;
        try {
            const result = await self.orm.call("pos.order", "get_orders_by_screen_id", [this.screen_id]);

            console.log('Screen ID:', this.screen_id);
            console.log('Orders:', result.orders);  // ✅ Giờ sẽ có data
            console.log('Order Lines:', result.order_lines);
            console.log('Screen Info:', result.screen_info);
        } catch (error) {
            console.error('Error loading order data:', error);
        }
    }

    async loadOrderData() {
        var self = this;
        try {
            //const result = await self.orm.call("pos.order", "get_orders_by_config_id", [self.config_id]);
            const result = await self.orm.call("pos.order", "get_orders_by_screen_id", [this.screen_id]);

            // ✅ LẤY config_id TỪ screen_info
            if (result['screen_info'] && result['screen_info'].config_id) {
                self.config_id = result['screen_info'].config_id;
            }

            self.state.order_details = result['orders'];
            self.state.order_lines = result['order_lines'];
            self.state.config_id = self.config_id;

            // Cập nhật số lượng đơn hàng - KHÔNG CẦN FILTER config_id vì server đã filter theo screen
            self.state.draft_count = self.state.order_details.filter((order) =>
                order.trcf_order_status == 'draft'
            ).length;

            self.state.waiting_count = self.state.order_details.filter((order) =>
                order.trcf_order_status == 'waiting'
            ).length;

            self.state.ready_count = self.state.order_details.filter((order) =>
                order.trcf_order_status == 'done'
            ).length;

            console.log('Order loaded:', self.state);
            console.log('Screen config_id:', self.config_id);

        } catch (error) {
            console.error('Error loading order data:', error);
        }
    }

    // ✅ =============  CÁC METHOD CẬP NHẬT TRẠNG THÁI =============
    async updateOrderStatus(orderId, newStatus, actionName = "cập nhật") {
        var self = this;

        // ✅ THÊM VÀO ARRAY
        if (!self.state.loadingOrders.includes(orderId)) {
            self.state.loadingOrders.push(orderId);
        }

        try {
            console.log(`🔄 ${actionName} đơn hàng ${orderId} -> ${newStatus}`);

            const result = await self.orm.call('pos.order', 'update_order_status', [orderId, newStatus]);

            if (result.success) {
                console.log(`✅ ${actionName} thành công:`, result);
                // Bus message sẽ tự động cập nhật UI, không cần reload ở đây
            } else {
                console.error(`❌ Lỗi ${actionName}:`, result.error);
                alert(`Không thể ${actionName}: ${result.error}`);
            }

        } catch (error) {
            console.error(`❌ Exception ${actionName}:`, error);
            alert(`Lỗi khi ${actionName} đơn hàng`);
        } finally {
            // ✅ XÓA KHỎI ARRAY
            const index = self.state.loadingOrders.indexOf(orderId);
            if (index > -1) {
                self.state.loadingOrders.splice(index, 1);
            }
        }
    }

    async updateOrderLineStatus(orderLineId, newStatus) {
        var self = this;

        const result = await self.orm.call('pos.order.line', 'update_order_line_status', [orderLineId, newStatus]);

        if (result.success) {
            console.log(`✅ cập nhật thành công:`, result);
            // Bus message sẽ tự động cập nhật UI, không cần reload ở đây
        } else {
            console.error(`❌ Lỗi cập nhật:`, result.error);
            alert(`Không thể cập nhật: ${result.error}`);
        }
    }

    // ✅ SHORTCUTS CHO CÁC TRẠNG THÁI
    async markAsDone(orderId) {
        await this.updateOrderStatus(orderId, 'done', 'hoàn thành');
    }

    async markOrderLineReady(orderLineId) {
        await this.updateOrderLineStatus(orderLineId, 'ready')
    }

    // KIỂM TRA ORDER ĐANG LOADING
    isOrderLoading(orderId) {
        return this.state.loadingOrders.includes(orderId);
    }

    // =============  HELPER METHODS =============
    // Lấy orders theo trạng thái - KHÔNG CẦN FILTER config_id vì server đã filter theo screen
    getOrdersByStatus(status) {
        return this.state.order_details.filter(order =>
            order.trcf_order_status === status
        );
    }

    // Lấy order lines của một đơn hàng
    getOrderLines(orderId) {
        return this.state.order_lines.filter(line =>
            line.order_id && line.order_id[0] === orderId
        );
    }

    getScreenIdFromURL() {
        const url = window.location.href;
        // Regex pattern
        const pattern = /action-\d+\/(\d+)\/action-/;
        const match = url.match(pattern);

        if (match) {
            return parseInt(match[1]);
        } else {
            return 1; // default
        }
    }

    // ============= TAILWIND HELPER METHODS =============

    // Tính thời gian tương đối
    getRelativeTime(dateString) {
        if (!dateString) return '';

        // Odoo trả về datetime theo UTC, thêm 'Z' để JavaScript parse đúng timezone
        const utcDateString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
        const orderDate = new Date(utcDateString);
        const now = new Date();
        const diffMs = now - orderDate;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Vừa xong';
        if (diffMins < 60) return `${diffMins} phút trước`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} giờ trước`;

        return `${Math.floor(diffHours / 24)} ngày trước`;
    }

    // Lấy class cho thời gian (màu sắc dựa trên độ trễ)
    getTimeClass(order) {
        if (!order.date_order) return 'text-gray-500';

        // Odoo trả về datetime theo UTC
        const utcDateString = order.date_order.endsWith('Z') ? order.date_order : order.date_order + 'Z';
        const orderDate = new Date(utcDateString);
        const now = new Date();
        const diffMins = Math.floor((now - orderDate) / 60000);

        if (diffMins >= 15) return 'text-red-500';  // Urgent - đỏ
        if (diffMins >= 5) return 'text-yellow-500'; // Warning - vàng
        return 'text-gray-500'; // Normal - xám
    }

    // Lấy class viền cho order card (dựa trên thời gian)
    getOrderBorderClass(order) {
        if (!order.date_order) return 'border border-gray-200';

        // Odoo trả về datetime theo UTC
        const utcDateString = order.date_order.endsWith('Z') ? order.date_order : order.date_order + 'Z';
        const orderDate = new Date(utcDateString);
        const now = new Date();
        const diffMins = Math.floor((now - orderDate) / 60000);

        if (diffMins >= 15) return 'border-2 border-red-500';  // Urgent
        if (diffMins >= 5) return 'border-2 border-yellow-400'; // Warning  
        return 'border border-gray-200'; // Normal
    }

}

// gán template
TrcfKitchenDashboard.template = "trcf_kitchen_screen.KitchenDashboardTemplate";

// Liên kết với tag trong ir.actions.client
registry.category("actions").add("kitchen_dashboard_tags", TrcfKitchenDashboard);
