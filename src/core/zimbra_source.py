import os
import re
import email
from email.header import decode_header
from typing import List
from datetime import datetime
from imapclient import IMAPClient
from .models import EmailMessage, EmailThread, Draft
from .email_source import EmailSource

class ZimbraSource(EmailSource):
    def __init__(self, host, username, password, email_address=None, name="Zimbra"):
        self.host = host
        self.username = username
        self.email_address = email_address or username
        self.password = password
        self.name = name
        self.client = None
        
        if not all([self.host, self.username, self.password]):
            raise ValueError(f"{self.name} IMAP credentials not found.")

    def authenticate(self) -> bool:
        try:
            if not self.client:
                self.client = IMAPClient(self.host, ssl=True)
                self.client.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"Zimbra authentication failed: {e}")
            return False

    def _decode_str(self, s):
        if not s:
            return ""
        decoded_list = decode_header(s)
        text, charset = decoded_list[0]
        if isinstance(text, bytes):
            return text.decode(charset or 'utf-8', errors='replace')
        return text

    def _get_body(self, msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode()
            except:
                pass
        return ""

    def get_recent_threads(self, limit=50) -> List[EmailThread]:
        if not self.authenticate():
            return []

        threads = {}

        def fetch_from_folder(folder_name):
            try:
                self.client.select_folder(folder_name)
                messages = self.client.search(['ALL'])
                if not messages:
                    return

                # Limit to the most recent 'limit' messages per folder
                messages = messages[-limit:]
                response = self.client.fetch(messages, ['ENVELOPE', 'RFC822', 'INTERNALDATE'])
                
                for msg_id, data in response.items():
                    raw_email = data[b'RFC822']
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = self._decode_str(msg.get("Subject", ""))
                    sender = self._decode_str(msg.get("From", ""))
                    
                    # ALWAYS use the IMAP INTERNALDATE. It is much more reliable than raw email Date headers
                    # which are frequently mangled or missing in Sent folders, causing them to falsely evaluate to datetime.now()
                    date = data.get(b'INTERNALDATE', datetime.now())
                    body = self._get_body(msg)
                    
                    # Robust, case-insensitive thread grouping
                    clean_subject = re.sub(r'^(re|fwd|fw|tr|aw):\s*', '', subject, flags=re.IGNORECASE).strip().lower()
                    if not clean_subject:
                        clean_subject = "(no subject)"
                    
                    email_msg = EmailMessage(
                        id=f"{folder_name}_{msg_id}",
                        subject=subject,
                        sender=sender,
                        body=body,
                        date=date,
                        is_unread=True
                    )
                    
                    if clean_subject not in threads:
                        threads[clean_subject] = EmailThread(id=clean_subject, subject=clean_subject, messages=[])
                        
                    threads[clean_subject].messages.append(email_msg)
            except Exception as e:
                print(f"Skipping folder {folder_name}: {e}")

        # Fetch from both INBOX and Sent
        fetch_from_folder('INBOX')
        fetch_from_folder('Sent')

        # Sort messages within each thread chronologically
        for t in threads.values():
            t.messages.sort(key=lambda x: x.date)

        # Sort the overall thread list by the latest message date
        thread_list = list(threads.values())
        thread_list.sort(key=lambda t: t.latest_message.date, reverse=True)
        return thread_list

    def save_draft(self, draft: Draft) -> bool:
        if not self.authenticate():
            return False
            
        # Create standard MIME email
        msg = email.message.EmailMessage()
        msg['Subject'] = draft.subject
        msg['To'] = draft.to_address
        msg['From'] = self.email_address
        msg.set_content(draft.body)
        
        try:
            self.client.append('Drafts', str(msg).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Failed to save draft to Zimbra: {e}")
            return False

    def get_source_name(self) -> str:
        return self.name
