/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";

patch(ClosePosPopup.prototype, {
    setup() {
        super.setup(...arguments);
        // Add owner withdrawal and next session opening to state
        this.state.trcf_owner_withdrawal = "0";
        this.state.trcf_next_session_opening = "0";
        this.state.trcf_loading = true;
        this.state.trcf_expenses = [];
        this.state.trcf_purchases = [];
        this.state.trcf_payment_income = {};  // {payment_method_id: amount}

        // Toggle states for collapsible sections
        this.state.trcf_show_cash_expenses = false;
        this.state.trcf_expanded_pm_expenses = {};
        this.state.trcf_expanded_pm_purchases = {};

        // Counted amounts for non-cash payment methods
        this.state.trcf_counted_amounts = {};

        // Load expenses and purchases asynchronously
        this.loadTrcfCashMoves();
    },

    // Load expenses and purchases from database
    async loadTrcfCashMoves() {
        const session = this.pos.session;

        // Convert datetime to UTC format without timezone (YYYY-MM-DD HH:MM:SS)
        const formatDateTimeUTC = (dateStr) => {
            if (!dateStr) return new Date().toISOString().slice(0, 19).replace('T', ' ');
            const date = new Date(dateStr);
            return date.toISOString().slice(0, 19).replace('T', ' ');
        };

        // Use session start time and current time (or stop time if closed)
        const startAt = formatDateTimeUTC(session.start_at);
        const stopAt = session.stop_at ? formatDateTimeUTC(session.stop_at) : formatDateTimeUTC(new Date());

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

        // Fetch purchase orders created after session started
        const purchases = await this.pos.data.searchRead(
            'purchase.order',
            [
                ['create_date', '>=', startAt],
                ['create_date', '<=', stopAt],
                ['trcf_payment_status', '=', 'paid'],
                ['state', '=', 'purchase'],
            ],
            ['name', 'amount_total', 'trcf_payment_method_id', 'trcf_payment_date', 'create_date', 'trcf_payment_status']
        );

        // Load payment income using new API (uses _read_group for efficiency)
        const paymentIncome = await this.pos.data.call(
            'pos.session',
            'get_payment_income_by_method',
            [session.id, startAt, stopAt]
        );

        // Store in reactive state to trigger re-render
        this.state.trcf_expenses = expenses || [];
        this.state.trcf_purchases = purchases || [];
        this.state.trcf_payment_income = paymentIncome || {};
        this.state.trcf_loading = false;
    },

    // Override cashMoveData to use trcf expenses and purchases
    get cashMoveData() {
        const moves = [];
        let total = 0;

        // Add expenses (negative amounts)
        (this.state.trcf_expenses || []).forEach((expense, i) => {
            const amount = -Math.abs(expense.trcf_amount || 0);
            moves.push({
                id: `expense_${i}`,
                name: `${_t('Chi phí')}: ${expense.name || 'N/A'}`,
                amount: amount,
            });
            total += amount;
        });

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

    // Calculate total of all payment methods (only income from orders, excluding opening)
    get totalAllPayments() {
        let total = 0;

        // Add cash payment if exists (amount - opening = income only)
        if (this.pos.config.cash_control && this.props.default_cash_details) {
            const cashOpening = this.props.default_cash_details.opening || 0;
            const cashAmount = this.props.default_cash_details.amount || 0;
            total += cashAmount - cashOpening;
        }

        // Add all non-cash payments (amount - opening = income only)
        if (this.props.non_cash_payment_methods) {
            this.props.non_cash_payment_methods.forEach(pm => {
                const pmOpening = pm.opening || 0;
                const pmAmount = pm.amount || 0;
                total += pmAmount - pmOpening;
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
        const expenses = (this.state.trcf_expenses || []).filter(expense => {
            if (expense.trcf_payment_method_id) {
                // Handle both integer ID and [id, name] array format
                const pmId = Array.isArray(expense.trcf_payment_method_id)
                    ? expense.trcf_payment_method_id[0]
                    : expense.trcf_payment_method_id;

                return pmId === paymentMethodId;
            }
            return false;
        });

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

    // Toggle payment method purchases visibility
    togglePMPurchases(paymentMethodId) {
        if (!this.state.trcf_expanded_pm_purchases) {
            this.state.trcf_expanded_pm_purchases = {};
        }
        this.state.trcf_expanded_pm_purchases[paymentMethodId] = !this.state.trcf_expanded_pm_purchases[paymentMethodId];
    },

    // Check if payment method purchases are expanded
    isPMPurchasesExpanded(paymentMethodId) {
        return this.state.trcf_expanded_pm_purchases && this.state.trcf_expanded_pm_purchases[paymentMethodId];
    },

    // Get purchases by payment method ID (returns total or array)
    getPurchasesByPaymentMethodId(paymentMethodId, returnArray = false) {
        const purchases = (this.state.trcf_purchases || []).filter(purchase => {
            if (purchase.trcf_payment_method_id) {
                // Handle both integer ID and [id, name] array format
                const pmId = Array.isArray(purchase.trcf_payment_method_id)
                    ? purchase.trcf_payment_method_id[0]
                    : purchase.trcf_payment_method_id;

                return pmId === paymentMethodId;
            }
            return false;
        });

        if (returnArray) {
            return purchases;
        }

        // Return total
        return purchases.reduce((sum, po) => sum + (po.amount_total || 0), 0);
    },

    // Calculate total of all purchases
    get totalAllPurchases() {
        let total = 0;
        (this.state.trcf_purchases || []).forEach((purchase) => {
            total += purchase.amount_total || 0;
        });
        return total;
    },

    // Calculate income from actual payment lines (excluding opening balance)
    // Now uses data loaded from database instead of looping through in-memory orders
    getPaymentIncomeByMethod(paymentMethodId) {
        // Use loaded data from database (persists after reload)
        return this.state.trcf_payment_income[paymentMethodId] || 0;
    },

    // Get all payment methods with their data for template
    getAllPaymentMethods() {
        const paymentMethods = [];

        // Add cash payment method if cash control is enabled
        if (this.props.default_cash_details) {
            const opening = this.props.default_cash_details.opening || 0;
            const cashPMId = this.props.default_cash_details.id || 'cash';

            // Calculate income from actual payment lines (most accurate method)
            const income = this.getPaymentIncomeByMethod(cashPMId);

            const expenseTotal = this.getExpensesByPaymentMethodId(cashPMId, false);
            const expenseDetails = this.getExpensesByPaymentMethodId(cashPMId, true);

            const purchaseTotal = this.getPurchasesByPaymentMethodId(cashPMId, false);
            const purchaseDetails = this.getPurchasesByPaymentMethodId(cashPMId, true);

            // Expected total = opening + income - expenses - purchases
            const expectedTotal = opening + income - expenseTotal - purchaseTotal;

            // Get counted from state, default to 0 if not entered
            const counted = this.state.trcf_counted_amounts[cashPMId] !== undefined
                ? parseFloat(this.state.trcf_counted_amounts[cashPMId] || 0)
                : 0;

            // Difference = counted - expected (positive = surplus/dư, negative = deficit/thiếu)
            const difference = counted - expectedTotal;

            const cashData = {
                id: cashPMId,
                name: this.props.default_cash_details.name?.toUpperCase() || _t('TIỀN MẶT'),
                opening: opening,
                income: income,
                expenses: expenseTotal,
                expenseDetails: expenseDetails,
                purchases: purchaseTotal,
                purchaseDetails: purchaseDetails,
                counted: counted,
                difference: difference,
                isCash: true,
            };

            paymentMethods.push(cashData);
        }

        // Add non-cash payment methods from props
        if (this.props.non_cash_payment_methods && this.props.non_cash_payment_methods.length > 0) {
            this.props.non_cash_payment_methods.forEach(pm => {
                // Force opening to 0 for non-cash methods as per user request
                const opening = 0;

                // Calculate income from actual payment lines (most accurate method)
                const income = this.getPaymentIncomeByMethod(pm.id);

                // Expenses and purchases are only for cash
                const expenseTotal = 0;
                const expenseDetails = [];

                const purchaseTotal = 0;
                const purchaseDetails = [];

                // Expected total = income only for non-cash
                const expectedTotal = income;

                // Get counted from state, default to 0 if not entered
                const counted = this.state.trcf_counted_amounts[pm.id] !== undefined
                    ? parseFloat(this.state.trcf_counted_amounts[pm.id] || 0)
                    : 0;

                // Difference = counted - expected (positive = surplus/dư, negative = deficit/thiếu)
                const difference = counted - expectedTotal;

                const pmData = {
                    id: pm.id,
                    name: pm.name?.toUpperCase() || 'UNKNOWN',
                    opening: opening,
                    income: income,
                    expenses: expenseTotal,
                    expenseDetails: expenseDetails,
                    purchases: purchaseTotal,
                    purchaseDetails: purchaseDetails,
                    counted: counted,
                    difference: difference,
                    isCash: false,
                };

                paymentMethods.push(pmData);
            });
        }

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

    // Get income for a payment method (excluding opening balance)
    getPaymentMethodIncome(paymentMethodId) {
        if (this.props.non_cash_payment_methods) {
            const pm = this.props.non_cash_payment_methods.find(p => p.id === paymentMethodId);
            if (pm) {
                const opening = pm.opening || 0;
                const amount = pm.amount || 0;
                return amount - opening;
            }
        }
        return 0;
    },

    // Calculate grand total (all remaining balances)
    get grandTotal() {
        let total = 0;

        // Add cash balance (opening + income - expenses)
        if (this.pos.config.cash_control && this.props.default_cash_details) {
            const cashOpening = this.props.default_cash_details.opening || 0;
            const cashAmount = this.props.default_cash_details.amount || 0;
            const cashIncome = cashAmount - cashOpening; // Exclude opening from income
            const cashExpenses = this.getExpensesByPaymentMethodId(cashPMId);
            const cashPurchases = this.getPurchasesByPaymentMethodId(cashPMId);
            total += cashOpening + cashIncome - cashExpenses - cashPurchases;
        }

        // Add non-cash balances (only income for non-cash)
        if (this.props.non_cash_payment_methods) {
            this.props.non_cash_payment_methods.forEach(pm => {
                const income = this.getPaymentIncomeByMethod(pm.id);
                total += income;
            });
        }

        return total;
    },

    // Calculate next session opening balance
    get nextSessionOpening() {
        // Get cash payment method ID
        const cashPMId = this.props.default_cash_details?.id || 'cash';

        // Get actual counted cash from input field
        const cashCounted = this.state.trcf_counted_amounts[cashPMId] !== undefined
            ? parseFloat(this.state.trcf_counted_amounts[cashPMId] || 0)
            : 0;

        const ownerWithdrawal = parseFloat(this.state.trcf_owner_withdrawal || "0");

        // Debug log
        console.log('🔍 nextSessionOpening - cashPMId:', cashPMId);
        console.log('🔍 nextSessionOpening - trcf_counted_amounts:', this.state.trcf_counted_amounts);
        console.log('🔍 nextSessionOpening - cashCounted:', cashCounted);
        console.log('🔍 nextSessionOpening - ownerWithdrawal:', ownerWithdrawal);
        console.log('🔍 nextSessionOpening - result:', cashCounted - ownerWithdrawal);

        if (!this.env.utils.isValidFloat(String(ownerWithdrawal))) {
            return 0;
        }

        // Next session opening = cash counted - owner withdrawal
        return cashCounted - ownerWithdrawal;
    },

    // Update counted amount for a payment method
    onCountedAmountChange(paymentMethodId, value) {
        // Explicitly save the value first (in case tModel hasn't updated yet)
        this.state.trcf_counted_amounts[paymentMethodId] = value;

        // If this is cash payment method, recalculate next session opening
        const cashPMId = this.props.default_cash_details?.id;

        if (paymentMethodId === cashPMId) {
            // Use nextTick to ensure state is updated before calculating
            Promise.resolve().then(() => {
                this.state.trcf_next_session_opening = String(this.nextSessionOpening);
            });
        }
    },

    // Update next session opening when owner withdrawal changes
    onOwnerWithdrawalChange(value) {
        this.state.trcf_owner_withdrawal = value;
        // Update the next session opening as a string number (not formatted)
        this.state.trcf_next_session_opening = String(this.nextSessionOpening);
    },

    // Override closeSession to save the new fields
    async closeSession() {
        // Save owner withdrawal and next session opening to pos.session
        if (this.env.utils.isValidFloat(this.state.trcf_owner_withdrawal)) {
            // Use the value from state instead of recalculating
            const nextSessionOpeningValue = parseFloat(this.state.trcf_next_session_opening || 0);

            await this.pos.data.call(
                "pos.session",
                "write",
                [[this.pos.session.id], {
                    trcf_owner_withdrawal: parseFloat(this.state.trcf_owner_withdrawal),
                    trcf_next_session_opening: nextSessionOpeningValue,
                }]
            );
        }

        // Save payment count data for each payment method
        const paymentMethods = this.getAllPaymentMethods();
        const paymentCountData = [];

        for (const pm of paymentMethods) {
            const countedAmount = this.state.trcf_counted_amounts[pm.id] !== undefined
                ? parseFloat(this.state.trcf_counted_amounts[pm.id] || 0)
                : 0;

            paymentCountData.push({
                session_id: this.pos.session.id,
                payment_method_id: pm.id,
                opening_amount: pm.opening || 0,
                income_amount: pm.income || 0,
                expense_amount: pm.expenses || 0,
                counted_amount: countedAmount,
            });
        }

        // Create or update payment count records
        if (paymentCountData.length > 0) {
            for (const data of paymentCountData) {
                // Check if record exists
                const existing = await this.pos.data.searchRead(
                    'trcf.pos.session.payment.count',
                    [
                        ['session_id', '=', data.session_id],
                        ['payment_method_id', '=', data.payment_method_id]
                    ],
                    ['id']
                );

                if (existing.length > 0) {
                    // Update existing record
                    await this.pos.data.call(
                        'trcf.pos.session.payment.count',
                        'write',
                        [[existing[0].id], data]
                    );
                } else {
                    // Create new record
                    await this.pos.data.call(
                        'trcf.pos.session.payment.count',
                        'create',
                        [data]
                    );
                }
            }
        }

        // Call original closeSession
        return super.closeSession(...arguments);
    },
});
