/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { useState } from "@odoo/owl";

patch(ClosePosPopup.prototype, {
    setup() {
        super.setup(...arguments);
        // Add owner withdrawal and next session opening to state
        this.state.trcf_owner_withdrawal = "0";
        this.state.trcf_next_session_opening = "0";
        this.state.trcf_loading = true;
        this.state.trcf_expenses = [];
        this.state.trcf_purchases = [];

        // Toggle states for collapsible sections
        this.state.trcf_show_cash_expenses = false;
        this.state.trcf_expanded_pm_expenses = {};

        // Counted amounts for non-cash payment methods
        this.state.trcf_counted_amounts = {};

        // Load expenses and purchases asynchronously
        this.loadTrcfCashMoves();
    },

    // Load expenses and purchases from database
    async loadTrcfCashMoves() {
        const session = this.pos.session;

        console.log('🔍 TRCF: Loading cash moves for session:', session.name);
        console.log('🔍 TRCF: Session start:', session.start_at);
        console.log('🔍 TRCF: Session stop:', session.stop_at);

        // Convert datetime to UTC format without timezone (YYYY-MM-DD HH:MM:SS)
        const formatDateTimeUTC = (dateStr) => {
            if (!dateStr) return new Date().toISOString().slice(0, 19).replace('T', ' ');
            const date = new Date(dateStr);
            return date.toISOString().slice(0, 19).replace('T', ' ');
        };

        // Use session start time and current time (or stop time if closed)
        const startAt = formatDateTimeUTC(session.start_at);
        const stopAt = session.stop_at ? formatDateTimeUTC(session.stop_at) : formatDateTimeUTC(new Date());

        console.log('🔍 TRCF: Filter start:', startAt);
        console.log('🔍 TRCF: Filter stop:', stopAt);

        // Fetch expenses created after session started (using create_date)
        const expenses = await this.pos.data.searchRead(
            'trcf.expense',
            [
                ['create_date', '>=', startAt],
                ['create_date', '<=', stopAt],
                ['state', '=', 'paid'],
            ],
            ['name', 'trcf_amount', 'trcf_payment_method_id', 'trcf_payment_date', 'create_date', 'state']
        );

        console.log('✅ TRCF: Loaded expenses:', expenses);
        console.log('✅ TRCF: Total expenses found:', expenses.length);

        // Store in reactive state to trigger re-render
        this.state.trcf_expenses = expenses || [];
        this.state.trcf_purchases = []; // Temporarily empty, will add later
        this.state.trcf_loading = false;

        console.log('✅ TRCF: Data stored in state, component should re-render');
    },

    // Override cashMoveData to use trcf expenses and purchases
    get cashMoveData() {
        console.log('💰 TRCF: Getting cashMoveData');
        console.log('💰 TRCF: Expenses:', this.state.trcf_expenses);

        const moves = [];
        let total = 0;

        // Add expenses (negative amounts)
        (this.state.trcf_expenses || []).forEach((expense, i) => {
            const amount = -Math.abs(expense.trcf_amount || 0);
            console.log(`💰 TRCF: Adding expense: ${expense.name} = ${amount}`);
            moves.push({
                id: `expense_${i}`,
                name: `Chi phí: ${expense.name || 'N/A'}`,
                amount: amount,
            });
            total += amount;
        });

        // Add purchases (negative amounts) - temporarily disabled
        // (this.state.trcf_purchases || []).forEach((purchase, i) => {
        //     const amount = -Math.abs(purchase.amount_total || 0);
        //     moves.push({
        //         id: `purchase_${i}`,
        //         name: `Mua hàng: ${purchase.name || 'N/A'}`,
        //         amount: amount,
        //     });
        //     total += amount;
        // });

        console.log('💰 TRCF: Total moves:', moves.length, 'Total amount:', total);
        return { total, moves };
    },

    // Calculate total payments from all payment methods
    get totalPayments() {
        let total = 0;
        for (const paymentId in this.state.payments) {
            const payment = this.state.payments[paymentId];
            const amount = parseFloat(payment.counted || payment.amount || "0");
            if (this.env.utils.isValidFloat(String(amount))) {
                total += amount;
            }
        }
        return total;
    },

    // Calculate cash expenses (only cash payment method expenses)
    get totalCashExpenses() {
        let total = 0;
        (this.state.trcf_expenses || []).forEach((expense) => {
            // Only count expenses paid with cash
            // Assuming cash payment method has a specific ID or name
            // For now, count all expenses as cash expenses
            total += Math.abs(expense.trcf_amount || 0);
        });
        return total;
    },

    // Calculate counted cash: total payments - cash expenses
    get countedCash() {
        return this.totalPayments - this.totalCashExpenses;
    },

    // Calculate total of all payment methods
    get totalAllPayments() {
        let total = 0;

        // Add cash payment if exists
        if (this.pos.config.cash_control && this.props.default_cash_details) {
            total += this.props.default_cash_details.amount || 0;
        }

        // Add all non-cash payments
        if (this.props.non_cash_payment_methods) {
            this.props.non_cash_payment_methods.forEach(pm => {
                total += pm.amount || 0;
            });
        }

        return total;
    },

    // Get opening balance for a payment method
    getPaymentMethodOpening(paymentMethodId) {
        if (this.state.payments && this.state.payments[paymentMethodId]) {
            return parseFloat(this.state.payments[paymentMethodId].opening || 0);
        }
        return 0;
    },

    // Get total cash expenses
    getCashExpenses() {
        let total = 0;
        (this.state.trcf_expenses || []).forEach((expense) => {
            // Check if payment method is cash
            if (expense.trcf_payment_method_id) {
                // Handle both integer ID and [id, name] format
                const pmId = Array.isArray(expense.trcf_payment_method_id)
                    ? expense.trcf_payment_method_id[0]
                    : expense.trcf_payment_method_id;

                // Check if it matches cash payment method ID from props
                const cashId = this.props.default_cash_details?.id || 4;

                if (pmId === cashId) {
                    total += expense.trcf_amount || 0;
                    return;
                }

                // Fallback: check name if available (only for array format)
                if (Array.isArray(expense.trcf_payment_method_id)) {
                    const pmName = expense.trcf_payment_method_id[1] || '';
                    if (pmName.toLowerCase().includes('cash') || pmName.toLowerCase().includes('tiền mặt')) {
                        total += expense.trcf_amount || 0;
                    }
                }
            }
        });
        return total;
    },

    // Get expenses by payment method (returns array for cash)
    getExpensesByPaymentMethod(type) {
        if (type === 'cash') {
            return (this.state.trcf_expenses || []).filter(expense => {
                if (expense.trcf_payment_method_id) {
                    // Handle both integer ID and [id, name] format
                    const pmId = Array.isArray(expense.trcf_payment_method_id)
                        ? expense.trcf_payment_method_id[0]
                        : expense.trcf_payment_method_id;

                    // Check if it matches cash payment method ID (usually 4 based on logs)
                    // Or check name if available
                    if (Array.isArray(expense.trcf_payment_method_id)) {
                        const pmName = expense.trcf_payment_method_id[1] || '';
                        return pmName.toLowerCase().includes('cash') || pmName.toLowerCase().includes('tiền mặt');
                    }
                    // If just ID, check against cash PM ID from props
                    return pmId === (this.props.default_cash_details?.id || 4);
                }
                return false;
            });
        }
        return [];
    },

    // Get expenses by payment method ID (returns total or array)
    getExpensesByPaymentMethodId(paymentMethodId, returnArray = false) {
        console.log(`🔍 TRCF: Getting expenses for payment method ID: ${paymentMethodId}`);
        console.log('🔍 TRCF: All expenses:', this.state.trcf_expenses);

        const expenses = (this.state.trcf_expenses || []).filter(expense => {
            console.log(`  - Expense: ${expense.name}, payment_method_id:`, expense.trcf_payment_method_id);
            if (expense.trcf_payment_method_id) {
                // Handle both integer ID and [id, name] array format
                const pmId = Array.isArray(expense.trcf_payment_method_id)
                    ? expense.trcf_payment_method_id[0]
                    : expense.trcf_payment_method_id;

                const matches = pmId === paymentMethodId;
                console.log(`    Payment method ID: ${pmId}, Matches ${paymentMethodId}? ${matches}`);
                return matches;
            }
            console.log('    No payment method ID');
            return false;
        });

        console.log(`✅ TRCF: Found ${expenses.length} expenses for payment method ${paymentMethodId}`);

        if (returnArray) {
            return expenses;
        }

        // Return total
        return expenses.reduce((sum, exp) => sum + (exp.trcf_amount || 0), 0);
    },

    // Calculate total of all expenses
    get totalAllExpenses() {
        let total = 0;
        (this.state.trcf_expenses || []).forEach((expense) => {
            total += expense.trcf_amount || 0;
        });
        return total;
    },

    // Toggle cash expenses visibility
    toggleCashExpenses() {
        this.state.trcf_show_cash_expenses = !this.state.trcf_show_cash_expenses;
    },

    // Toggle payment method expenses visibility
    togglePMExpenses(paymentMethodId) {
        if (!this.state.trcf_expanded_pm_expenses) {
            this.state.trcf_expanded_pm_expenses = {};
        }
        this.state.trcf_expanded_pm_expenses[paymentMethodId] = !this.state.trcf_expanded_pm_expenses[paymentMethodId];
    },

    // Check if payment method expenses are expanded
    isPMExpensesExpanded(paymentMethodId) {
        return this.state.trcf_expanded_pm_expenses && this.state.trcf_expanded_pm_expenses[paymentMethodId];
    },

    // Get all payment methods with their data for template
    getAllPaymentMethods() {
        console.log('🔍 TRCF: getAllPaymentMethods called');
        console.log('🔍 TRCF: this.props:', this.props);

        const paymentMethods = [];

        // Add cash payment method if cash control is enabled
        if (this.props.default_cash_details) {
            console.log('💰 TRCF: Cash control enabled, default_cash_details:', this.props.default_cash_details);

            const opening = this.props.default_cash_details.opening || 0;
            const income = this.props.default_cash_details.amount || 0;
            const expenseTotal = this.getCashExpenses();
            const expenseDetails = this.getExpensesByPaymentMethod('cash');

            // Get cash payment method ID from props
            const cashPMId = this.props.default_cash_details.id || 'cash';

            // Get counted from existing Odoo input
            const counted = this.state.payments && this.state.payments[cashPMId]
                ? parseFloat(this.state.payments[cashPMId].counted || this.state.payments[cashPMId].amount || 0)
                : income;

            const difference = opening + income - expenseTotal - counted;

            const cashData = {
                id: cashPMId,
                name: this.props.default_cash_details.name?.toUpperCase() || 'TIỀN MẶT',
                opening: opening,
                income: income,
                expenses: expenseTotal,
                expenseDetails: expenseDetails,
                counted: counted,
                difference: difference,
                isCash: true,
            };

            console.log('💰 TRCF: Adding cash payment method:', cashData);
            paymentMethods.push(cashData);
        } else {
            console.log('ℹ️ TRCF: No default_cash_details in props');
        }

        // Add non-cash payment methods from props
        if (this.props.non_cash_payment_methods && this.props.non_cash_payment_methods.length > 0) {
            console.log('💳 TRCF: Non-cash payment methods from props:', this.props.non_cash_payment_methods);

            this.props.non_cash_payment_methods.forEach(pm => {
                const opening = pm.opening || 0;
                const income = pm.amount || 0;
                const expenseTotal = this.getExpensesByPaymentMethodId(pm.id, false);
                const expenseDetails = this.getExpensesByPaymentMethodId(pm.id, true);

                // Get counted from state or default to income
                const counted = this.state.trcf_counted_amounts[pm.id] !== undefined
                    ? parseFloat(this.state.trcf_counted_amounts[pm.id] || 0)
                    : income;

                const difference = opening + income - expenseTotal - counted;

                const pmData = {
                    id: pm.id,
                    name: pm.name?.toUpperCase() || 'UNKNOWN',
                    opening: opening,
                    income: income,
                    expenses: expenseTotal,
                    expenseDetails: expenseDetails,
                    counted: counted,
                    difference: difference,
                    isCash: false,
                };

                console.log(`💳 TRCF: Adding ${pm.name}:`, pmData);
                paymentMethods.push(pmData);
            });
        } else {
            console.log('ℹ️ TRCF: No non_cash_payment_methods in props');
        }

        console.log('✅ TRCF: Total payment methods to display:', paymentMethods.length);
        console.log('✅ TRCF: Payment methods array:', paymentMethods);
        return paymentMethods;
    },

    // Get cash payment method
    getCashPaymentMethod() {
        if (!this.pos || !this.pos.payment_methods) {
            return null;
        }
        return this.pos.payment_methods.find(pm => pm.type === 'cash');
    },

    // Get non-cash payment methods
    getNonCashPaymentMethods() {
        // In Odoo 19, payment methods come from props, not pos.payment_methods
        if (!this.props.non_cash_payment_methods) {
            return [];
        }

        return this.props.non_cash_payment_methods;
    },

    // Get income for a payment method
    getPaymentMethodIncome(paymentMethodId) {
        if (this.props.non_cash_payment_methods) {
            const pm = this.props.non_cash_payment_methods.find(p => p.id === paymentMethodId);
            return pm ? (pm.amount || 0) : 0;
        }
        return 0;
    },

    // Calculate grand total (all remaining balances)
    get grandTotal() {
        let total = 0;

        // Add cash balance (opening + income - expenses)
        if (this.pos.config.cash_control && this.props.default_cash_details) {
            const cashOpening = this.props.default_cash_details.opening || 0;
            const cashIncome = this.props.default_cash_details.amount || 0;
            const cashExpenses = this.getCashExpenses();
            total += cashOpening + cashIncome - cashExpenses;
        }

        // Add non-cash balances
        if (this.props.non_cash_payment_methods) {
            this.props.non_cash_payment_methods.forEach(pm => {
                const opening = (pm.type === 'bank' && pm.number !== 0) ? this.getPaymentMethodOpening(pm.id) : 0;
                const income = pm.amount || 0;
                const expenses = this.getExpensesByPaymentMethodId(pm.id);
                total += opening + income - expenses;
            });
        }

        return total;
    },

    // Calculate next session opening balance
    get nextSessionOpening() {
        const cashCounted = this.countedCash;
        const ownerWithdrawal = parseFloat(this.state.trcf_owner_withdrawal || "0");

        if (!this.env.utils.isValidFloat(String(ownerWithdrawal))) {
            return 0;
        }

        return cashCounted - ownerWithdrawal;
    },

    // Update counted amount for a payment method
    onCountedAmountChange(paymentMethodId, value) {
        this.state.trcf_counted_amounts[paymentMethodId] = value;
    },

    // Update next session opening when owner withdrawal changes
    onOwnerWithdrawalChange(value) {
        this.state.trcf_owner_withdrawal = value;
        // Update the next session opening as a string number (not formatted)
        this.state.trcf_next_session_opening = String(this.nextSessionOpening);
    },

    // Override closeSession to save the new fields
    async closeSession() {
        // Save owner withdrawal and next session opening
        if (this.env.utils.isValidFloat(this.state.trcf_owner_withdrawal)) {
            await this.pos.data.call(
                "pos.session",
                "write",
                [[this.pos.session.id], {
                    trcf_owner_withdrawal: parseFloat(this.state.trcf_owner_withdrawal),
                    trcf_next_session_opening: this.nextSessionOpening,
                }]
            );
        }

        // Call original closeSession
        return super.closeSession(...arguments);
    },
});
