#!/bin/bash

# Script to install MOMO Payment Terminal module to Odoo

ODOO_ADDONS_PATH="/opt/odoo/addons"  # Change this to your Odoo addons path
MODULE_NAME="momo_payment_terminal"
CURRENT_DIR="$(pwd)"

echo "Installing MOMO Payment Terminal Module..."
echo "==========================================="

# Check if running from module directory
if [ ! -f "__manifest__.py" ]; then
    echo "Error: Please run this script from the momo_payment_terminal directory"
    exit 1
fi

# Ask for Odoo addons path
read -p "Enter your Odoo addons path (default: $ODOO_ADDONS_PATH): " USER_PATH
if [ ! -z "$USER_PATH" ]; then
    ODOO_ADDONS_PATH="$USER_PATH"
fi

# Check if path exists
if [ ! -d "$ODOO_ADDONS_PATH" ]; then
    echo "Error: Odoo addons path does not exist: $ODOO_ADDONS_PATH"
    exit 1
fi

# Copy module
echo "Copying module to $ODOO_ADDONS_PATH/$MODULE_NAME..."
sudo cp -r "$CURRENT_DIR" "$ODOO_ADDONS_PATH/$MODULE_NAME"

# Set permissions
echo "Setting permissions..."
sudo chown -R odoo:odoo "$ODOO_ADDONS_PATH/$MODULE_NAME"
sudo chmod -R 755 "$ODOO_ADDONS_PATH/$MODULE_NAME"

echo ""
echo "Installation complete!"
echo "====================="
echo "Next steps:"
echo "1. Restart Odoo service: sudo systemctl restart odoo"
echo "2. Go to Apps → Update Apps List"
echo "3. Search for 'MOMO Payment Terminal' and install"
echo "4. Configure in Point of Sale → Configuration → Payment Methods"
echo ""
echo "For detailed instructions, see README.md"
