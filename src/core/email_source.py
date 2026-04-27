from abc import ABC, abstractmethod
from typing import List
from .models import EmailThread, Draft

class EmailSource(ABC):
    """Base class for all email sources."""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticates with the email provider."""
        pass
        
    @abstractmethod
    def get_recent_threads(self, limit: int = 50) -> List[EmailThread]:
        """Fetches a list of recent email threads."""
        pass
        
    @abstractmethod
    def save_draft(self, draft: Draft) -> bool:
        """Saves a draft to the provider's Drafts folder."""
        pass
        
    @abstractmethod
    def get_source_name(self) -> str:
        """Returns the name of the source (e.g., 'Outlook', 'Zimbra')."""
        pass
