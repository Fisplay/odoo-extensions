import json
from unittest.mock import patch
from odoo.tests.common import TransactionCase


class TestAIBookkeeping(TransactionCase):

    def setUp(self):
        """Set up test environment: vendors, accounts, invoices, and invoice lines."""
        super().setUp()

        # Create a vendor
        self.vendor = self.env["res.partner"].create({
            "name": "Test Vendor",
            "supplier_rank": 1,  # Mark as a supplier
        })

        # Create bookkeeping accounts
        self.account_expense = self.env["account.account"].create({
            "name": "Test Expense Account",
            "code": "6000",
            "user_type_id": self.env.ref("account.data_account_type_expenses").id,
        })

        self.account_alternative = self.env["account.account"].create({
            "name": "Alternative Expense Account",
            "code": "6001",
            "user_type_id": self.env.ref("account.data_account_type_expenses").id,
        })

        # Create tax
        self.tax_21 = self.env["account.tax"].create({
            "name": "VAT 21%",
            "amount": 21,
            "type_tax_use": "purchase",
        })

        # Create a draft vendor invoice
        self.invoice = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.vendor.id,
            "state": "draft",
            "amount_total": 100.0,
            "ref": "INV-TEST-001",
        })

        # Add invoice line with missing bookkeeping details
        self.invoice_line = self.env["account.move.line"].create({
            "move_id": self.invoice.id,
            "name": "Test Product",
            "quantity": 1,
            "price_unit": 100.0,
            "account_id": False,  # To be filled by AI
            "tax_ids": [(6, 0, [])],  # To be filled by AI
        })

    @patch("odoo.addons.your_module.models.account_move.AccountMove.env")
    def test_ai_bookkeeping_suggestions(self, mock_env):
        """Test AI Bookkeeping Assist updates invoice lines correctly."""

        # Mock the AI response
        ai_response = [
            {
                "line_id": self.invoice_line.id,
                "product": "Test Product",
                "description": "Test Product",
                "price": 100.0,
                "account_id": self.account_expense.id,
                "account_name": self.account_expense.name,
                "analytic_distribution": {},
                "analytic_distribution_ids": {},
                "tax_ids": [self.tax_21.id],
                "tax_names": ["VAT 21%"],
            }
        ]

        mock_ai_service = mock_env["openai.service"]
        mock_ai_service.get_openai_response.return_value = json.dumps(ai_response)

        # Execute action
        self.invoice.action_ai_bookkeeping_assist()

        # Reload invoice line to check updates
        self.invoice_line.refresh()

        # Verify if AI-suggested account is applied
        self.assertEqual(self.invoice_line.account_id.id, self.account_expense.id, "AI should assign the correct account.")

        # Verify if AI-suggested tax is applied
        self.assertEqual(self.invoice_line.tax_ids.ids, [self.tax_21.id], "AI should assign the correct tax.")

        # Ensure the message post log exists
        messages = self.invoice.message_ids.mapped("body")
        self.assertTrue(any("✅ AI-based bookkeeping account" in msg for msg in messages), "Success message should be logged.")

