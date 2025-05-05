"""Legal document RAG implementation."""

import logging
from typing import Any, List, Optional, Tuple
from uuid import uuid4

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from ..context.context_manager import ContextManager
from .base import BaseRAG

logger = logging.getLogger(__name__)

class LegalRAG(BaseRAG):
    """RAG implementation specialized for legal document processing."""

    def __init__(
        self,
        document_processor: Any,
        context_manager: Optional[ContextManager] = None,
        **kwargs: Any
    ):
        """Initialize the legal RAG system.

        Args:
            document_processor: Document processor instance.
            context_manager: Optional context manager instance.
            **kwargs: Additional arguments for base RAG.
        """
        super().__init__(document_processor=document_processor, **kwargs)
        self.context_manager = context_manager

    def _init_prompts(self) -> None:
        """Initialize prompt templates for legal document processing."""
        self.qa_template = PromptTemplate(
            input_variables=["context", "query", "conversation_history"],
            template="""你是一個專業的法律助理，請根據提供的上下文和對話歷史回答問題。

對話歷史：
{conversation_history}

上下文資訊：
{context}

問題：{query}

請根據上述資訊回答問題。如果無法從上下文中找到答案，請明確說明。
回答時請：
1. 保持專業的法律用語
2. 引用相關法條或判例（如果上下文中有提供）
3. 提供清晰的論述
4. 如果有需要，提供額外的解釋

回答："""
        )

        self.summary_template = PromptTemplate(
            input_variables=["context", "document_history"],
            template="""請總結以下法律文件的主要內容，並考慮文件的歷史版本：

文件歷史：
{document_history}

當前文件內容：
{context}

請提供：
1. 案件類型
2. 主要爭議點
3. 法院判決要點
4. 重要法條引用
5. 與歷史版本的主要差異

總結："""
        )

    def _prepare_conversation_history(
        self,
        conversation_id: Optional[str] = None,
        last_n: int = 5
    ) -> str:
        """Prepare conversation history for context.

        Args:
            conversation_id: Optional conversation ID.
            last_n: Number of last messages to include.

        Returns:
            Formatted conversation history.
        """
        if not self.context_manager or not conversation_id:
            return "無對話歷史"

        history = self.context_manager.get_conversation_history(
            conversation_id=conversation_id,
            last_n=last_n
        )

        if not history:
            return "無對話歷史"

        formatted = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _prepare_document_history(self, doc_id: str) -> str:
        """Prepare document version history.

        Args:
            doc_id: Document ID.

        Returns:
            Formatted document history.
        """
        if not self.context_manager:
            return "無文件歷史"

        context = self.context_manager.get_document_context(doc_id)
        if not context or not context.references:
            return "無文件歷史"

        formatted = []
        for ref in context.references:
            version = ref.get("version", "unknown")
            date = ref.get("date", "unknown")
            changes = ref.get("changes", "無變更說明")
            formatted.append(f"版本 {version} ({date}): {changes}")

        return "\n".join(formatted)

    def retrieve(
        self,
        query: str,
        k: int = 4,
        min_score: float = 0.3,
        conversation_id: Optional[str] = None,
        **kwargs: Any
    ) -> List[Document]:
        """Retrieve relevant legal documents.

        Args:
            query: Query text.
            k: Number of documents to retrieve.
            min_score: Minimum similarity score.
            conversation_id: Optional conversation ID for context.
            **kwargs: Additional retrieval arguments.

        Returns:
            List of relevant documents.
        """
        # Add query to conversation history if available
        if self.context_manager and conversation_id:
            self.context_manager.add_message(
                conversation_id=conversation_id,
                message={
                    "role": "user",
                    "content": query,
                    "timestamp": kwargs.get("timestamp")
                }
            )

        results = self.document_processor.search_similar(
            query=query,
            k=k,
            **kwargs
        )

        # Convert to LangChain documents
        documents = []
        for result in results:
            score = 1.0 - (result.get("distance", 0) or 0)
            if score >= min_score:
                doc = Document(
                    page_content=result["document"],
                    metadata={
                        **result["metadata"],
                        "score": score
                    }
                )
                documents.append(doc)

                # Add to document context if available
                if self.context_manager:
                    self.context_manager.add_document_context(
                        doc_id=result["metadata"].get("doc_id", str(uuid4())),
                        title=result["metadata"].get("title", "Unknown"),
                        content=result["document"],
                        metadata=result["metadata"]
                    )

        return documents

    def generate(
        self,
        query: str,
        context: List[Document],
        mode: str = "qa",
        conversation_id: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Generate response for legal queries.

        Args:
            query: User query.
            context: Retrieved documents.
            mode: Generation mode ("qa" or "summary").
            conversation_id: Optional conversation ID.
            **kwargs: Additional generation arguments.

        Returns:
            Generated response.
        """
        if not context:
            return "抱歉，我找不到相關的法律文件來回答您的問題。"

        # Prepare context text
        context_text = "\n\n".join(
            f"文件 {i+1}（相關度：{doc.metadata.get('score', 0):.2f}）：\n{doc.page_content}"
            for i, doc in enumerate(context)
        )

        # Get conversation history if available
        conversation_history = self._prepare_conversation_history(
            conversation_id=conversation_id
        ) if mode == "qa" else ""

        # Get document history for summary mode
        document_history = ""
        if mode == "summary" and len(context) > 0:
            doc_id = context[0].metadata.get("doc_id")
            if doc_id:
                document_history = self._prepare_document_history(doc_id)

        # Select template based on mode
        if mode == "summary":
            chain = LLMChain(
                llm=self.llm,
                prompt=self.summary_template
            )
            response = chain.run(
                context=context_text,
                document_history=document_history
            )
        else:  # qa mode
            chain = LLMChain(
                llm=self.llm,
                prompt=self.qa_template
            )
            response = chain.run(
                context=context_text,
                query=query,
                conversation_history=conversation_history
            )

        # Add response to conversation history
        if self.context_manager and conversation_id:
            self.context_manager.add_message(
                conversation_id=conversation_id,
                message={
                    "role": "assistant",
                    "content": response,
                    "timestamp": kwargs.get("timestamp")
                }
            )

        return response

    def summarize(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[str, List[Document]]:
        """Summarize relevant legal documents.

        Args:
            query: Search query to find relevant documents.
            conversation_id: Optional conversation ID.
            **kwargs: Additional arguments.

        Returns:
            Tuple of (summary, retrieved documents).
        """
        documents = self.retrieve(
            query=query,
            conversation_id=conversation_id,
            **kwargs
        )
        summary = self.generate(
            query=query,
            context=documents,
            mode="summary",
            conversation_id=conversation_id
        )
        return summary, documents
