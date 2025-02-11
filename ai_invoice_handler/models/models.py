import csv

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"  # Extends the existing account.move model

    def action_ai_bookkeeping_assist(self):
        """Triggered by the contextual action to fetch AI-based bookkeeping, analytic, and tax suggestions."""

        openai_service = self.env["openai.service"]  # Access AI service

        for invoice in self:
            # Ensure only draft vendor invoices are processed
            if invoice.move_type != "in_invoice" or invoice.state != "draft":
                invoice.message_post(body="⚠️ AI Bookkeeping Assist can only be applied to draft vendor invoices.")
                continue

            vendor_id = invoice.partner_id.id

            # Fetch last 5 purchase invoices for the same vendor
            previous_invoices = self.env["account.move"].search([
                ("partner_id", "=", vendor_id),
                ("move_type", "=", "in_invoice"),
                ("state", "=", "posted")  # Only posted invoices
            ], order="invoice_date desc", limit=5)

            # Fetch all bookkeeping accounts for reference
            accounts = self.env["account.account"].search([])
            account_mapping = {str(acc.id): acc.name for acc in accounts}  # Create an ID-to-name mapping

            # Extract bookkeeping accounts, analytic distribution, tax information, and line descriptions
            history_data = []
            for inv in previous_invoices:
                for line in inv.invoice_line_ids:
                    tax_ids = ",".join(str(tax.id) for tax in line.tax_ids)  # Store tax IDs as a comma-separated string
                    tax_names = ",".join(tax.name for tax in line.tax_ids)  # Store tax names

                    # Ensure analytic_distribution is always treated as a dictionary
                    analytic_distribution = line.analytic_distribution or {}
                    if isinstance(analytic_distribution, str):
                        analytic_distribution = {}

                    history_data.append([
                        line.product_id.name or "Unknown",
                        line.name or "No Description",
                        line.account_id.id if line.account_id else "",
                        line.account_id.name if line.account_id else "Unknown",
                        str(analytic_distribution).replace(",", ";"),  # Avoid CSV parsing issues
                        str({str(k): v for k, v in analytic_distribution.items()}).replace(",", ";"),
                        tax_ids,  # Store tax IDs
                        tax_names  # Store tax names
                    ])

            # Extract current invoice lines with placeholders and IDs
            current_lines = []
            for line in invoice.invoice_line_ids:
                current_lines.append([
                    line.id,  # Store invoice line ID for mapping back
                    line.product_id.name or "Unknown",
                    line.name or "No Description",
                    line.price_unit,
                    "[TO_BE_FILLED]",  # Placeholder for account ID
                    "[TO_BE_FILLED]",  # Placeholder for account name
                    "[TO_BE_FILLED]",  # Placeholder for analytic distribution
                    "[TO_BE_FILLED]",  # Placeholder for analytic distribution IDs
                    "[TO_BE_FILLED]",  # Placeholder for tax IDs
                    "[TO_BE_FILLED]"   # Placeholder for tax names
                ])

            # Convert data to CSV format
            def list_to_csv(data_list):
                return "\n".join([",".join(map(str, row)) for row in data_list])

            history_csv = list_to_csv(history_data)
            current_csv = list_to_csv(current_lines)
            account_mapping_csv = "\n".join([f"{acc_id},{acc_name}" for acc_id, acc_name in account_mapping.items()])

            # Create AI prompt
            prompt = f"""
            You are an expert accountant analyzing bookkeeping data. Your task is to determine the most appropriate bookkeeping account, analytic distribution, and tax selection for the current invoice based on past invoices.

            ### Account Mapping (Reference for Account Selection):
            Account ID,Account Name
            {account_mapping_csv}

            ### Previous Invoice Data (CSV Format):
            Product,Description,Account ID,Account Name,Analytic Distribution,Analytic Distribution IDs,Tax IDs,Tax Names
            {history_csv}

            ### Current Invoice Data (CSV Format):
            Line ID,Product,Description,Price,Account ID,Account Name,Analytic Distribution,Analytic Distribution IDs,Tax IDs,Tax Names
            {current_csv}

            **Your task:** Fill in the missing 'Account ID', 'Account Name', 'Analytic Distribution', 'Analytic Distribution IDs', 'Tax IDs', and 'Tax Names' based on past data.

            **Important:** 🚨 Only return the filled CSV, nothing else. No explanations, no extra text. Just output the filled CSV using the same format as 'Current Invoice Data'.
            """

            # Post prompt into chatter for debugging
            invoice.message_post(body=f"📌 AI Debugging Prompt:\n<pre>{prompt}</pre>")

            # Call OpenAI via the AI service
            ai_response = openai_service.get_openai_response(prompt)

            if "Error" in ai_response:
                invoice.message_post(body=f"⚠️ AI Bookkeeping Assist Error: {ai_response}")
                continue  # Skip processing this invoice if there's an error

            # Parse AI response (expected CSV)
            reader = csv.reader(ai_response.split("\n"))
            next(reader)  # Skip headers

            suggestion_map = {}
            for row in reader:
                if len(row) < 10:
                    continue  # Skip invalid rows

                (
                    line_id, product, description, price, account_id, account_name,
                    analytic_distribution, analytic_distribution_ids, tax_ids, tax_names
                ) = row

                suggestion_map[line_id] = {
                    "account_id": account_id.strip(),
                    "account_name": account_name.strip(),
                    "analytic_distribution": analytic_distribution.strip(),
                    "analytic_distribution_ids": analytic_distribution_ids.strip(),
                    "tax_ids": tax_ids.strip(),
                    "tax_names": tax_names.strip()
                }

            # Loop through invoice lines and apply AI suggestions
            for line in invoice.invoice_line_ids:
                suggestion = suggestion_map.get(str(line.id))
                if not suggestion:
                    continue  # Skip if no AI suggestion found for this line

                # Get suggested account
                suggested_account_id = suggestion["account_id"]
                suggested_account_name = suggestion["account_name"]

                # Ensure account exists in Odoo
                suggested_account = self.env["account.account"].browse(int(suggested_account_id)) if suggested_account_id.isdigit() else None
                if not suggested_account or not suggested_account.exists():
                    suggested_account = self.env["account.account"].search([("name", "=", suggested_account_name)], limit=1)

                # Assign account if found
                if suggested_account and suggested_account.exists():
                    line.account_id = suggested_account.id

                # Assign analytic distribution
                analytic_distribution = suggestion["analytic_distribution"]
                if analytic_distribution and analytic_distribution != "[TO_BE_FILLED]":
                    line.analytic_distribution = eval(analytic_distribution)

                # Assign tax selection
                tax_id_list = [int(tid) for tid in suggestion["tax_ids"].split(",") if tid.isdigit()]
                if tax_id_list:
                    taxes = self.env["account.tax"].browse(tax_id_list)
                else:
                    # If tax IDs are not valid, try to fetch by name
                    tax_names = suggestion["tax_names"].split(",")
                    taxes = self.env["account.tax"].search([("name", "in", tax_names)])

                line.tax_ids = [(6, 0, taxes.ids)] if taxes else []

            invoice.message_post(body="✅ AI-based bookkeeping account, analytic distribution, and tax selection applied.")
