"""Base classes for RAG system."""

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Tuple

from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import Document

from ..processors.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class BaseRAG(ABC):
    """Abstract base class for RAG implementations.

    This class defines the interface for RAG systems that combine
    retrieval and generation for legal document processing.
    """

    def __init__(
        self,
        document_processor: DocumentProcessor,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        streaming: bool = True
    ):
        """Initialize the RAG system.

        Args:
            document_processor: Document processor instance for retrieval.
            model_name: Name of the LLM model to use.
            temperature: Temperature for LLM generation.
            streaming: Whether to stream LLM output.
        """
        self.document_processor = document_processor

        # Initialize LLM
        callbacks = [StreamingStdOutCallbackHandler()] if streaming else None
        callback_manager = CallbackManager(callbacks) if callbacks else None

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            streaming=streaming,
            callback_manager=callback_manager
        )

        # Initialize default prompt templates
        self._init_prompts()

        logger.info(f"Initialized RAG system with model {model_name}")

    @abstractmethod
    def _init_prompts(self) -> None:
        """Initialize prompt templates for the RAG system."""
        pass

    @abstractmethod
    def retrieve(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Document]:
        """Retrieve relevant documents for the query.

        Args:
            query: Query text.
            **kwargs: Additional retrieval arguments.

        Returns:
            List of relevant documents.
        """
        pass

    @abstractmethod
    def generate(
        self,
        query: str,
        context: List[Document],
        **kwargs: Any
    ) -> str:
        """Generate response based on query and retrieved context.

        Args:
            query: User query.
            context: Retrieved documents for context.
            **kwargs: Additional generation arguments.

        Returns:
            Generated response.
        """
        pass

    def query(
        self,
        query: str,
        **kwargs: Any
    ) -> Tuple[str, List[Document]]:
        """Process a query through the RAG pipeline.

        Args:
            query: User query.
            **kwargs: Additional arguments for retrieval and generation.

        Returns:
            Tuple of (generated response, retrieved documents).
        """
        # Retrieve relevant documents
        documents = self.retrieve(query, **kwargs)

        # Generate response
        response = self.generate(query, documents, **kwargs)

        return response, documents
