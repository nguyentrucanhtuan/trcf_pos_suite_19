# TRCF POS Expenses

## Overview
Simple expense management module for COFFEETREE with POS payment method integration.

## Features
- ✅ Expense categories management
- ✅ Expense tracking with auto-generated references (EXP/YYYY/XXXX)
- ✅ Integration with POS payment methods
- ✅ Simple workflow: Draft → Paid
- ✅ Comprehensive filtering and search
- ✅ Kanban view for visual management
- ✅ Activity tracking and chatter

## Models

### Expense Category (`trcf.expense.category`)
- Category name and code
- Description
- Active/Archive status
- Expense count

### Expense (`trcf.expense`)
- Auto-generated reference
- Name and description
- Category
- Amount
- Payment method (POS)
- Payment status and date
- State (draft/paid)
- Created by user
- Notes and chatter

## Installation
1. Copy module to custom_addons directory
2. Update apps list in Odoo
3. Install "TRCF POS Expenses" module

## Usage
1. Create expense categories (Office Supplies, Utilities, etc.)
2. Create expenses and assign to categories
3. Select payment method
4. Mark as paid when payment is completed

## Dependencies
- base
- point_of_sale
