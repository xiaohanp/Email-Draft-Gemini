from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class EmailMessage:
    id: str
    subject: str
    sender: str
    body: str
    date: datetime
    is_unread: bool

@dataclass
class EmailThread:
    id: str
    subject: str
    messages: List[EmailMessage]
    
    @property
    def latest_message(self) -> EmailMessage:
        return self.messages[-1] if self.messages else None
        
    def get_context(self) -> str:
        """Returns a string representation of the thread for the LLM."""
        context = ""
        for msg in self.messages:
            context += f"From: {msg.sender}\n"
            context += f"Date: {msg.date}\n"
            context += f"Subject: {msg.subject}\n"
            context += f"Body:\n{msg.body}\n"
            context += "-" * 40 + "\n"
        return context

@dataclass
class Draft:
    thread_id: str
    subject: str
    body: str
    to_address: str
