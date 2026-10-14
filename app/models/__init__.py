# Import every model so SQLAlchemy can resolve string relationships
# (e.g. User.documents -> "Document") no matter which model a script uses.
from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.role import Role
from app.models.user import User

__all__ = [
    "Conversation",
    "Message",
    "Document",
    "DocumentChunk",
    "Role",
    "User",
]
