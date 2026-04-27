import os
import json
import google.generativeai as genai
from datetime import datetime

class GeminiDrafter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-3-flash-preview")
        
    def classify_email(self, thread_context: str) -> str:
        """Classifies the email to decide if a draft is needed."""
        prompt = f"""
        Classify the following email thread into one of these categories:
        - URGENT: Requires immediate attention.
        - NEEDS_REPLY: A standard email that needs a response.
        - FYI: Informational, no reply needed.
        - AUTOMATED: Newsletter, receipt, alert, etc. No reply needed.
        
        Email Thread:
        {thread_context}
        
        Respond with ONLY the category name.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip().upper()

    def draft_reply(self, thread_context: str, my_persona: str, language: str = "English") -> str:
        """Generates a draft reply based on the thread context."""
        prompt = f"""
You are drafting a reply on behalf of the user.
User Persona: {my_persona}

Here is the full email thread (most recent last):
---
{thread_context}
---

Write a draft reply IN {language.upper()}. Be concise and match the tone of prior replies.
Do NOT send — this is a draft for human review.
Return only the reply body, no subject line.

If you don't have enough context to write a confident reply, output [NEEDS_CONTEXT] instead.
"""
        response = self.model.generate_content(prompt)
        draft = response.text.strip()
        
        self._log_draft(thread_context, draft)
        return draft

    def refine_draft(self, thread_context: str, my_persona: str, current_draft: str, adjustment: str) -> str:
        """Refines an existing draft based on a user's prompt."""
        prompt = f"""
You are drafting a reply on behalf of the user.
User Persona: {my_persona}

Here is the full email thread (most recent last):
---
{thread_context}
---

Here is the CURRENT DRAFT of your reply:
---
{current_draft}
---

The user has requested the following adjustment to the current draft:
"{adjustment}"

Please rewrite the draft incorporating the user's instructions.
Return ONLY the revised reply body, no subject line, no extra conversational filler.
"""
        response = self.model.generate_content(prompt)
        new_draft = response.text.strip()
        
        self._log_draft(thread_context, new_draft)
        return new_draft

    def _log_draft(self, context: str, draft: str):
        """Audit log for debugging and tuning."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "draft": draft
        }
        
        os.makedirs("logs", exist_ok=True)
        with open("logs/draft_audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
