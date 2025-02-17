import openai
from odoo import models, fields, api

class OpenAIService(models.Model):
    _name = "openai.service"
    _description = "OpenAI API Service"

    api_key = fields.Char(string="API Key", required=True)

    @api.model
    def get_openai_response(self, prompt):
        """Call OpenAI API and return response using chat completion."""
        api_key = self.env["ir.config_parameter"].sudo().get_param("openai.api_key")
        if not api_key:
            return "API key not configured"

        try:
            client = openai.OpenAI(api_key=api_key)  # Initialize client
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content  # Correct response format
        except Exception as e:
            return f"Error: {str(e)}"

    @api.model
    def get_assistant_response(self, assistant_id, prompt):
        """Call OpenAI Assistants API with an Assistant ID and user prompt."""
        api_key = self.env["ir.config_parameter"].sudo().get_param("openai.api_key")
        if not api_key:
            return "API key not configured"

        try:
            client = openai.OpenAI(api_key=api_key)  # Initialize OpenAI client
            
            # Step 1: Create a new thread
            thread = client.beta.threads.create()
            thread_id = thread.id  # Get the newly created thread ID

            # Step 2: Add user message (prompt) to the thread
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )

            # Step 3: Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )

            # Step 4: Poll for completion
            while run.status not in ["completed", "failed"]:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)  # FIXED

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                return messages.data[0].content[0].text.value  # Extract response
            else:
                return "Assistant failed to generate a response."

        except Exception as e:
            return f"Error: {str(e)}"