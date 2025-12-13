/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component, onWillStart, useState, onMounted, markup } = owl;
import { useService } from "@web/core/utils/hooks";

export class TrcfKitchenDashboard extends Component {
    setup(env) {

        super.setup();
        this.busService = this.env.services.bus_service;

        // ✅ LẤY SCREEN ID TỪ URL odoo/action-xxx/SCREEN_ID/action-yyy
        this.screen_id = this.getScreenIdFromURL();

        // ✅ SETUP DEBOUNCING & DUPLICATE TRACKING
        this.pendingOrderUpdates = new Set();
        this.pendingLineUpdates = new Set();
        this.updateTimer = null;
        this.DEBOUNCE_DELAY = 300; // 300ms

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
            screen_name: 'Đơn Hàng Bếp',  // ✅ Tên màn hình
            screen_category_ids: [],  // ✅ Category IDs của screen để filter
            stages: 'draft',
            draft_count: 0,
            waiting_count: 0,
            ready_count: 0,
            loadingOrders: [],
            loadingOrderLines: [],  // Track loading state cho từng món
            showRecipe: false,  // Toggle hiển thị công thức
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

        // ✅ XỬ LÝ ĐƠN MỚI - INCREMENTAL UPDATE
        if (message.message === "pos_order_created"
            && message.res_model === "pos.order"
            && message.config_id) {

            // PHÁT ÂM THANH THÔNG BÁO
            self.playNotificationSound();

            // ✅ THÊM TRỰC TIẾP VÀO STATE - KHÔNG RELOAD
            if (message.order_data && message.order_lines) {
                self.addNewOrderIncremental(message.order_data, message.order_lines);
            } else {
                // Fallback - nếu không có data thì mới fetch
                self.loadOrderData();
            }

            return;
        }


        // ✅ XỬ LÝ CẬP NHẬT TRẠNG THÁI ĐƠN - DEBOUNCED
        if (message.message === "pos_order_status_updated" &&
            message.res_model === "pos.order" &&
            message.config_id == self.config_id) {

            // Thêm vào pending queue
            self.pendingOrderUpdates.add({
                order_id: message.order_id,
                new_status: message.new_status,
                old_status: message.old_status
            });

            // Debounce update
            self.scheduleUpdate();

            return;
        }

        // ✅ XỬ LÝ CẬP NHẬT TRẠNG THÁI MÓN - DEBOUNCED
        if (message.message === "pos_order_line_status_updated" &&
            message.res_model === "pos.order.line") {

            self.pendingLineUpdates.add({
                line_id: message.line_id,
                new_status: message.new_status
            });

            self.scheduleUpdate();

            return;
        }
    }

    async loadOrderData_test() {
        var self = this;
        try {
            const result = await self.orm.call("pos.order", "get_orders_by_screen_id", [this.screen_id]);

        } catch (error) {
            console.error('Error loading order data:', error);
        }
    }

    async loadOrderData() {
        var self = this;
        try {
            //const result = await self.orm.call("pos.order", "get_orders_by_config_id", [self.config_id]);
            const result = await self.orm.call("pos.order", "get_orders_by_screen_id", [this.screen_id]);

            // ✅ LẤY config_id, screen_name VÀ categories TỪ screen_info
            if (result['screen_info']) {
                const screenInfo = result['screen_info'];  // ✅ Object, không phải array!
                self.config_id = screenInfo.config_id || null;
                self.state.screen_name = screenInfo.screen_name || 'Đơn Hàng Bếp';
                self.state.screen_category_ids = screenInfo.categories || [];  // ✅ Lưu category IDs
            }

            // ✅ CẬP NHẬT STATE
            self.state.order_details = result['orders'] || [];
            self.state.order_lines = result['order_lines'] || [];

            // ✅ CẬP NHẬT COUNTERS
            self.updateCounters();

        } catch (error) {
            console.error('Error loading order data:', error);
        }
    }

    // ✅ =============  CÁC METHOD CẬP NHẬT TRẠNG THÁI =============
    async updateOrderStatus(orderId, newStatus, actionName = 'Cập nhật') {
        var self = this;

        // ✅ Thêm vào loading state
        if (!self.state.loadingOrders.includes(orderId)) {
            self.state.loadingOrders.push(orderId);
        }

        try {
            const result = await this.orm.call(
                "pos.order",
                "update_order_status",
                [orderId, newStatus]
            );

            if (result.success) {
                // ✅ Không xóa loading ngay - chờ bus message
                // Loading state sẽ được xóa khi nhận bus message
            } else {
                // ❌ Lỗi - xóa loading ngay
                const index = self.state.loadingOrders.indexOf(orderId);
                if (index > -1) {
                    self.state.loadingOrders.splice(index, 1);
                }
                console.error(`Lỗi ${actionName}:`, result.message);
            }
        } catch (error) {
            // ❌ Lỗi - xóa loading ngay
            const index = self.state.loadingOrders.indexOf(orderId);
            if (index > -1) {
                self.state.loadingOrders.splice(index, 1);
            }
            console.error(`Lỗi ${actionName}:`, error);
        }
    }

    async updateOrderLineStatus(orderLineId, newStatus) {
        try {
            const result = await this.orm.call(
                "pos.order.line",
                "update_order_line_status",
                [orderLineId, newStatus]
            );

            if (!result.success) {
                console.error('Lỗi cập nhật:', result.message);
            }
        } catch (error) {
            console.error('Lỗi cập nhật:', error);
        }
    }

    // ✅ SHORTCUTS CHO CÁC TRẠNG THÁI
    async markAsDone(orderId) {
        await this.updateOrderStatus(orderId, 'done', 'hoàn thành');
    }

    async markOrderLineReady(orderLineId) {
        var self = this;

        // ✅ Thêm vào loading state
        if (!self.state.loadingOrderLines.includes(orderLineId)) {
            self.state.loadingOrderLines.push(orderLineId);
        }

        // ✅ Gọi API - loading state sẽ được xóa khi nhận bus message
        await this.updateOrderLineStatus(orderLineId, 'ready');
        // Note: Loading state được xóa trong processPendingUpdates() khi nhận bus message
    }

    // Kiểm tra order line đang loading
    isOrderLineLoading(orderLineId) {
        return this.state.loadingOrderLines.includes(orderLineId);
    }

    // KIỂM TRA ORDER ĐANG LOADING
    isOrderLoading(orderId) {
        return this.state.loadingOrders.includes(orderId);
    }

    // TOGGLE HIỂN THỊ CÔNG THỨC
    toggleRecipe() {
        this.state.showRecipe = !this.state.showRecipe;
    }

    // ✅ =============  INCREMENTAL UPDATE METHODS =============

    /**
     * THÊM ĐƠN MỚI VÀO STATE - KHÔNG RELOAD TOÀN BỘ
     */
    addNewOrderIncremental(orderData, orderLinesData) {
        var self = this;

        // ✅ KIỂM TRA ĐƠN ĐÃ TỒN TẠI CHƯA - TRÁNH DUPLICATE
        const existingIndex = self.state.order_details.findIndex(
            o => o.id === orderData.id
        );

        if (existingIndex === -1) {
            // ✅ CHƯA TỒN TẠI → THÊM MỚI
            self.state.order_details.push(orderData);

            // ✅ FILTER ORDER LINES THEO SCREEN CATEGORY
            const filteredLines = orderLinesData.filter(line => {
                // Nếu screen không có category, không hiện món nào
                if (!self.state.screen_category_ids || self.state.screen_category_ids.length === 0) {
                    return false;
                }

                // Check nếu product có category nào match với screen
                // product_id.pos_categ_ids là array of category IDs
                const productCategories = line.product_id_pos_categ_ids || [];
                return productCategories.some(catId =>
                    self.state.screen_category_ids.includes(catId)
                );
            });

            // ✅ THÊM CHỈ NHỮNG LINES ĐÃ FILTER
            filteredLines.forEach(line => {
                const lineExists = self.state.order_lines.some(
                    l => l.id === line.id
                );
                if (!lineExists) {
                    self.state.order_lines.push(line);
                }
            });

            // ✅ CẬP NHẬT COUNTERS
            self.updateCounters();
        }
    }

    /**
     * SCHEDULE UPDATE - DEBOUNCE NHIỀU UPDATES
     */
    scheduleUpdate() {
        var self = this;

        // Clear timer cũ
        if (self.updateTimer) {
            clearTimeout(self.updateTimer);
        }

        // Set timer mới - chỉ update 1 lần sau DEBOUNCE_DELAY
        self.updateTimer = setTimeout(() => {
            self.processPendingUpdates();
        }, self.DEBOUNCE_DELAY);
    }

    /**
     * XỬ LÝ TẤT CẢ PENDING UPDATES CÙNG LÚC
     */
    processPendingUpdates() {
        var self = this;

        // Xử lý order updates
        if (self.pendingOrderUpdates.size > 0) {
            self.pendingOrderUpdates.forEach(update => {
                const orderIndex = self.state.order_details.findIndex(o => o.id === update.order_id);
                if (orderIndex !== -1) {
                    self.state.order_details[orderIndex].trcf_order_status = update.new_status;
                }

                // ✅ Xóa loading state
                const loadingIndex = self.state.loadingOrders.indexOf(update.order_id);
                if (loadingIndex > -1) {
                    self.state.loadingOrders.splice(loadingIndex, 1);
                }
            });
            self.pendingOrderUpdates.clear();
        }

        // Xử lý line updates
        if (self.pendingLineUpdates.size > 0) {
            self.pendingLineUpdates.forEach(update => {
                const lineIndex = self.state.order_lines.findIndex(l => l.id === update.line_id);
                if (lineIndex !== -1) {
                    self.state.order_lines[lineIndex].trcf_order_status = update.new_status;
                }

                // ✅ Xóa loading state
                const loadingIndex = self.state.loadingOrderLines.indexOf(update.line_id);
                if (loadingIndex > -1) {
                    self.state.loadingOrderLines.splice(loadingIndex, 1);
                }
            });
            self.pendingLineUpdates.clear();
        }

        // Cập nhật counters
        self.updateCounters();
    }

    /**
     * CẬP NHẬT COUNTERS - CHỈ ĐẾM VISIBLE ORDERS
     */
    updateCounters() {
        var self = this;

        // ✅ CHỈ ĐẾM ORDERS CÓ MÓN (visible)
        const visibleOrders = self.state.order_details.filter(order =>
            self.hasVisibleLines(order.id)
        );

        self.state.draft_count = visibleOrders.filter(
            order => order.trcf_order_status == 'draft'
        ).length;

        self.state.waiting_count = visibleOrders.filter(
            order => order.trcf_order_status == 'waiting'
        ).length;

        self.state.ready_count = visibleOrders.filter(
            order => order.trcf_order_status == 'done'
        ).length;
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

    // ✅ Kiểm tra order có món nào visible không
    hasVisibleLines(orderId) {
        return this.getOrderLines(orderId).length > 0;
    }

    // Render HTML content (cho công thức)
    renderHtml(htmlString) {
        if (!htmlString) return '';
        return markup(htmlString);
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
