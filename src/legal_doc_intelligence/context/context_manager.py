"""Context management system for legal document processing."""

import json
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConversationContext(BaseModel):
    """Model for conversation context."""

    conversation_id: str
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentContext(BaseModel):
    """Model for document context."""

    doc_id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    references: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContextManager:
    """Manager for handling conversation and document context.

    Features:
    1. Conversation history management
    2. Document context tracking
    3. Context persistence
    4. Context retrieval and update
    5. Context pruning and cleanup
    """

    def __init__(
        self,
        max_conversation_history: int = 10,
        persist_dir: Optional[Path] = None
    ):
        """Initialize the context manager.

        Args:
            max_conversation_history: Maximum number of messages to keep in history.
            persist_dir: Directory for context persistence.
        """
        self.max_conversation_history = max_conversation_history
        self.persist_dir = persist_dir

        if persist_dir:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self.conversations_dir = persist_dir / "conversations"
            self.documents_dir = persist_dir / "documents"
            self.conversations_dir.mkdir(exist_ok=True)
            self.documents_dir.mkdir(exist_ok=True)

        # Active contexts
        self.active_conversations: Dict[str, Deque[Dict[str, Any]]] = {}
        self.active_documents: Dict[str, DocumentContext] = {}

        logger.info(
            f"Initialized ContextManager with max_history={max_conversation_history}"
        )

    def _save_conversation(self, conversation_id: str) -> None:
        """Save conversation context to disk.

        Args:
            conversation_id: ID of the conversation to save.
        """
        if not self.persist_dir:
            return

        conversation = list(self.active_conversations[conversation_id])
        context = ConversationContext(
            conversation_id=conversation_id,
            messages=conversation
        )

        path = self.conversations_dir / f"{conversation_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(context.model_dump(), f, ensure_ascii=False, default=str)

    def _save_document_context(self, doc_id: str) -> None:
        """Save document context to disk.

        Args:
            doc_id: ID of the document to save.
        """
        if not self.persist_dir:
            return

        context = self.active_documents[doc_id]
        path = self.documents_dir / f"{doc_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(context.model_dump(), f, ensure_ascii=False, default=str)

    def _load_conversation(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load conversation context from disk.

        Args:
            conversation_id: ID of the conversation to load.

        Returns:
            List of conversation messages if found.
        """
        if not self.persist_dir:
            return None

        path = self.conversations_dir / f"{conversation_id}.json"
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            context = ConversationContext(**data)
            return context.messages

    def _load_document_context(self, doc_id: str) -> Optional[DocumentContext]:
        """Load document context from disk.

        Args:
            doc_id: ID of the document to load.

        Returns:
            Document context if found.
        """
        if not self.persist_dir:
            return None

        path = self.documents_dir / f"{doc_id}.json"
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return DocumentContext(**data)

    def add_message(
        self,
        conversation_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Add a message to conversation history.

        Args:
            conversation_id: Conversation ID.
            message: Message to add.
        """
        if conversation_id not in self.active_conversations:
            # Try to load existing conversation
            existing = self._load_conversation(conversation_id)
            if existing:
                self.active_conversations[conversation_id] = deque(
                    existing,
                    maxlen=self.max_conversation_history
                )
            else:
                self.active_conversations[conversation_id] = deque(
                    maxlen=self.max_conversation_history
                )

        self.active_conversations[conversation_id].append(message)
        self._save_conversation(conversation_id)

    def get_conversation_history(
        self,
        conversation_id: str,
        last_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history.

        Args:
            conversation_id: Conversation ID.
            last_n: Optional number of last messages to return.

        Returns:
            List of conversation messages.
        """
        if conversation_id not in self.active_conversations:
            existing = self._load_conversation(conversation_id)
            if existing:
                self.active_conversations[conversation_id] = deque(
                    existing,
                    maxlen=self.max_conversation_history
                )
            else:
                return []

        history = list(self.active_conversations[conversation_id])
        if last_n:
            history = history[-last_n:]
        return history

    def add_document_context(
        self,
        doc_id: str,
        title: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add or update document context.

        Args:
            doc_id: Document ID.
            title: Document title.
            content: Document content.
            metadata: Document metadata.
        """
        context = DocumentContext(
            doc_id=doc_id,
            title=title,
            content=content,
            metadata=metadata
        )
        self.active_documents[doc_id] = context
        self._save_document_context(doc_id)

    def get_document_context(self, doc_id: str) -> Optional[DocumentContext]:
        """Get document context.

        Args:
            doc_id: Document ID.

        Returns:
            Document context if found.
        """
        if doc_id not in self.active_documents:
            context = self._load_document_context(doc_id)
            if context:
                self.active_documents[doc_id] = context

        return self.active_documents.get(doc_id)

    def add_document_reference(
        self,
        doc_id: str,
        reference: Dict[str, Any]
    ) -> None:
        """Add a reference to document context.

        Args:
            doc_id: Document ID.
            reference: Reference information.
        """
        context = self.get_document_context(doc_id)
        if context:
            context.references.append(reference)
            context.updated_at = datetime.utcnow()
            self._save_document_context(doc_id)

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history.

        Args:
            conversation_id: Conversation ID to clear.
        """
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]

        if self.persist_dir:
            path = self.conversations_dir / f"{conversation_id}.json"
            if path.exists():
                path.unlink()

    def clear_document_context(self, doc_id: str) -> None:
        """Clear document context.

        Args:
            doc_id: Document ID to clear.
        """
        if doc_id in self.active_documents:
            del self.active_documents[doc_id]

        if self.persist_dir:
            path = self.documents_dir / f"{doc_id}.json"
            if path.exists():
                path.unlink()

    def cleanup_old_contexts(self, max_age_days: int = 30) -> None:
        """Clean up old context files.

        Args:
            max_age_days: Maximum age of context files in days.
        """
        if not self.persist_dir:
            return

        cutoff = datetime.utcnow().timestamp() - (max_age_days * 24 * 3600)

        # Clean up conversations
        for path in self.conversations_dir.glob("*.json"):
            if path.stat().st_mtime < cutoff:
                path.unlink()

        # Clean up documents
        for path in self.documents_dir.glob("*.json"):
            if path.stat().st_mtime < cutoff:
                path.unlink()
