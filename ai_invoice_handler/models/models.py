import json
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"  # Extends the existing account.move model

    def action_ai_bookkeeping_assist(self):
        """Triggered by the contextual action to fetch AI-based bookkeeping, analytic, and tax suggestions."""

        openai_service = self.env["openai.service"]  # Access AI service

        # Fetch system parameters
        debug_enabled = self.env["ir.config_parameter"].sudo().get_param("ai_invoice_handler.debug", "false").lower() == "true"
        assistant_id = self.env["ir.config_parameter"].sudo().get_param("openai.assistant_id")

        if not assistant_id:
            self.message_post(body="⚠️ AI Bookkeeping Assist Error: No Assistant ID configured.")
            return

        for invoice in self:
            if invoice.move_type != "in_invoice" or invoice.state != "draft":
                invoice.message_post(body="⚠️ AI Bookkeeping Assist can only be applied to draft vendor invoices.")
                continue

            vendor_id = invoice.partner_id.id

            # Fetch last 5 purchase invoices for the same vendor
            previous_invoices = self.env["account.move"].search([
                ("partner_id", "=", vendor_id),
                ("move_type", "=", "in_invoice"),
                ("state", "=", "posted")
            ], order="invoice_date desc", limit=5)

            # Extract history data
            history_data = []
            for inv in previous_invoices:
                for line in inv.invoice_line_ids:
                    tax_ids = [tax.id for tax in line.tax_ids]
                    tax_names = [tax.name for tax in line.tax_ids]

                    analytic_distribution = line.analytic_distribution or {}
                    if isinstance(analytic_distribution, str):
                        analytic_distribution = {}

                    history_data.append({
                        "invoice_sum": inv.amount_total,
                        "invoice_ref": inv.ref or "No Reference",
                        "product": line.product_id.name or "Unknown",
                        "description": line.name or "No Description",
                        "account_id": line.account_id.id if line.account_id else None,
                        "account_name": line.account_id.name if line.account_id else "Unknown",
                        "analytic_distribution": analytic_distribution,
                        "analytic_distribution_ids": {str(k): v for k, v in analytic_distribution.items()},
                        "tax_ids": tax_ids,
                        "tax_names": tax_names
                    })

            # Extract current invoice lines
            current_lines = []
            for line in invoice.invoice_line_ids:
                current_lines.append({
                    "line_id": line.id,
                    "invoice_sum": invoice.amount_total,
                    "invoice_ref": invoice.ref or "No Reference",
                    "product": line.product_id.name or "Unknown",
                    "description": line.name or "No Description",
                    "price": line.price_unit,
                    "account_id": "[TO_BE_FILLED]",
                    "account_name": "[TO_BE_FILLED]",
                    "analytic_distribution": "[TO_BE_FILLED]",
                    "analytic_distribution_ids": "[TO_BE_FILLED]",
                    "tax_ids": "[TO_BE_FILLED]",
                    "tax_names": "[TO_BE_FILLED]"
                })

            # Create AI prompt
            prompt = f"""
            You are an expert accountant analyzing bookkeeping data. Your task is to determine the most appropriate bookkeeping account, analytic distribution, and tax selection for the current invoice based on past invoices.
            
            ### Previous Invoice Data:
            {json.dumps(history_data, indent=2)}

            ### Current Invoice Data:
            {json.dumps(current_lines, indent=2)}

            **Your task:** Fill in the missing 'account_id', 'account_name', 'analytic_distribution', 'analytic_distribution_ids', 'tax_ids', and 'tax_names' based on past data.

            **Important Considerations:**
            - If an invoice's reference ('invoice_ref') matches a previous one, prioritize it when determining correct accounts and tax selection.
            - If an invoice sum ('invoice_sum') is similar to a past one, it's likely the same type of transaction.
            - 🚨 Only return valid JSON. No explanations, no extra text. Just output the JSON formatted result matching the structure of 'Current Invoice Data'.
            """

            # Post prompt into chatter for debugging if enabled
            if debug_enabled:
                invoice.message_post(body=f"📌 AI Debugging Prompt:\n<pre>{prompt}</pre>")

            # Call OpenAI Assistant API
            ai_response = openai_service.get_assistant_response(assistant_id, prompt)

            # Debug raw response
            if debug_enabled:
                invoice.message_post(body=f"🔍 AI Debugging Response:\n<pre>{ai_response}</pre>")

            if "Error" in ai_response:
                invoice.message_post(body=f"⚠️ AI Bookkeeping Assist Error: {ai_response}")
                continue  # Skip processing this invoice if there's an error

            try:
                gpt_suggestion = json.loads(ai_response)
            except json.JSONDecodeError:
                invoice.message_post(body="⚠️ AI Bookkeeping Assist Error: Invalid JSON response from AI.")
                continue  # Skip processing if AI response is invalid

            # Loop through invoice lines and apply AI suggestions
            for suggestion in gpt_suggestion:
                line_id = suggestion.get("line_id")
                invoice_line = invoice.invoice_line_ids.filtered(lambda l: l.id == line_id)
                if not invoice_line:
                    continue  # Skip if no matching invoice line found

                invoice_line = invoice_line[0]

                # Get suggested account
                suggested_account_id = suggestion.get("account_id")
                suggested_account_name = suggestion.get("account_name")

                suggested_account = None
                if suggested_account_id:
                    suggested_account = self.env["account.account"].browse(suggested_account_id)
                if not suggested_account or not suggested_account.exists():
                    suggested_account = self.env["account.account"].search([("name", "=", suggested_account_name)], limit=1)

                # Assign account if found
                if suggested_account and suggested_account.exists():
                    invoice_line.account_id = suggested_account.id

                # Assign analytic distribution
                analytic_distribution = suggestion.get("analytic_distribution")
                if analytic_distribution and analytic_distribution != "[TO_BE_FILLED]":
                    invoice_line.analytic_distribution = analytic_distribution

                # Assign tax selection
                tax_ids = suggestion.get("tax_ids", [])
                tax_names = suggestion.get("tax_names", [])

                taxes = self.env["account.tax"].browse(tax_ids) if tax_ids else None
                if not taxes or not taxes.exists():
                    taxes = self.env["account.tax"].search([("name", "in", tax_names)])

                if taxes:
                    invoice_line.tax_ids = [(6, 0, taxes.ids)]

            invoice.message_post(body="✅ AI-based bookkeeping account, analytic distribution, and tax selection applied.")
