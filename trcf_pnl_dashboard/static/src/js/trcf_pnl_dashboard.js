/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TrcfPnlDashboard extends Component {
    setup() {

        this.notification = useService("notification");
        this.orm = useService("orm");

        this.state = useState({
            isLoading: true,
            expenseCategories: [],
            expenses: []
        })

        this.data = {
            currentMonth: "2023-11",
            totalRevenue: 50000000,
            totalExpense: 25000000,
            grossProfit: 25000000,
            netProfit: 18000000,
            revenueDetails: [
                { name: 'Doanh thu bán đồ uống', amount: 40000000 },
                { name: 'Doanh thu bán đồ ăn nhẹ', amount: 8000000 },
                { name: 'Doanh thu bán hàng hóa khác', amount: 2000000 }
            ],
            profitDetails: [
                { name: 'Doanh thu thuần', amount: 50000000, type: 'positive' },
                { name: 'Giá vốn hàng bán (Chi phí nguyên vật liệu)', amount: 10000000, type: 'negative' },
                { name: 'Lợi nhuận gộp', amount: 40000000, type: 'positive', isTotal: true },
                { name: 'Chi phí hoạt động (lương, thuê, điện nước, marketing, vv)', amount: 15000000, type: 'negative' },
                { name: 'Lợi nhuận ròng (trước thuế)', amount: 25000000, type: 'positive', isTotal: true }
            ]
        };

        // Load dữ liệu khi component khởi tạo
        onWillStart(async () => {
            await this.loadExpenseCategories();
            await this.loadExpenses();
        });
    }

    /**
     * Load danh sách expense categories từ Odoo
     */
    async loadExpenseCategories() {
        try {
            this.state.isLoading = true;
             
            const categories = await this.orm.searchRead(
                'product.product',
                [
                    ['can_be_expensed', '=', true],  // ✅ Key field: products có thể dùng cho expense
                    ['active', '=', true]
                ],
                [
                    'id', 
                    'name', 
                    'default_code',           // Mã sản phẩm
                    'categ_id',              // Category của product
                    'uom_id',                // Unit of measure
                    'standard_price',        // Giá chuẩn
                    'description',           // Mô tả
                    'company_id'             // Công ty
                ],
                { order: 'id asc' }
            );
            
            // console.log('✅ Raw result:', categories);
            this.state.expenseCategories = categories || [];
                        
        } catch (error) {
            console.error('Error loading expense categories:', error);
            this.notification.add(
                'Không thể tải danh sách loại chi phí. Sử dụng dữ liệu mặc định.',
                { type: 'warning' }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    async loadExpenses() {
        try {
            this.state.isLoading = true;
             
            const expenses = await this.orm.searchRead(
                'hr.expense',
                [
                    ['product_id', '!=', false], // Chỉ lấy expenses có danh mục
                ],
                [],
                { order: 'date desc, id desc' }
            );
            
            console.log('✅ Raw result:', expenses);
            this.state.expenses = expenses || [];
                        
        } catch (error) {
            console.error('Error loading expense categories:', error);
            this.notification.add(
                'Không thể tải danh sách chi phí. Sử dụng dữ liệu mặc định.',
                { type: 'warning' }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN').format(amount) + ' VNĐ';
    }

    getAmountClass(type) {
        if (type === 'positive') {
            return 'trcf_positive';
        } else if (type === 'negative') {
            return 'trcf_negative';
        }
        return 'trcf_neutral';
    }

    getProfitCardClass(amount) {
        return amount > 0 ? 'trcf_card trcf_profit_card' : 'trcf_card';
    }

    calculateCategoryTotals(expense_category_id) {
        let total = 0;                          
        const expenses = this.state.expenses;   
        
        for (const expen of expenses) {
            if (expen.product_id[0] === expense_category_id) {
                total += expen.total_amount;   
            }
        }
        
        return total;
    }

    calculateExpenseTotal() {
        let total = 0;                          
        const expenses = this.state.expenses;   
        
        for (const expen of expenses) {
            total += expen.total_amount;   
        }

        return total;
    }
}

TrcfPnlDashboard.template = "trcf_pnl_dashboard.dashboard_template";

// Đăng ký component
registry.category("actions").add("trcf_pnl_dashboard_action", TrcfPnlDashboard);