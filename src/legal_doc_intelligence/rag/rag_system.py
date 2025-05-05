"""RAG (Retrieval-Augmented Generation) system implementation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.callbacks import get_openai_callback
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from loguru import logger

from ..processors.vectorization_processor import VectorizationProcessor


class LegalRAGSystem:
    """RAG system for legal document question answering."""

    def __init__(
        self,
        vectorization_processor: VectorizationProcessor,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> None:
        """Initialize the RAG system.

        Args:
            vectorization_processor: Processor for document vectorization and retrieval.
            model_name: Name of the LLM model to use.
            temperature: Temperature parameter for the LLM.
            max_tokens: Maximum tokens for LLM response.
        """
        self.vectorization_processor = vectorization_processor
        self.llm = OpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Initialize prompt templates
        self.qa_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""你是一個專業的法律助理，請基於以下文件內容回答問題。
            請使用繁體中文回答。
            如果無法從文件中找到答案，請明確說明。

            文件內容：
            {context}

            問題：
            {question}

            回答："""
        )

        self.qa_chain = LLMChain(
            llm=self.llm,
            prompt=self.qa_template
        )

        logger.info("Initialized Legal RAG system")

    def _prepare_context(self, documents: List[Dict[str, Any]], max_length: int = 3000) -> str:
        """Prepare context from retrieved documents.

        Args:
            documents: List of retrieved documents.
            max_length: Maximum context length.

        Returns:
            Prepared context string.
        """
        context = []
        current_length = 0

        for doc in documents:
            doc_text = doc["document"]
            if current_length + len(doc_text) > max_length:
                # Truncate the document to fit within max_length
                remaining_length = max_length - current_length
                if remaining_length > 100:  # Only add if we can include meaningful content
                    doc_text = doc_text[:remaining_length]
                    context.append(doc_text)
                break

            context.append(doc_text)
            current_length += len(doc_text)

            # Add metadata if available
            if "metadata" in doc:
                meta_str = f"\n來源：{doc['metadata'].get('court_name', '未知法院')}"
                if doc['metadata'].get('decision_date'):
                    meta_str += f", 日期：{doc['metadata']['decision_date']}"
                context.append(meta_str)

        return "\n\n".join(context)

    async def answer_question(
        self,
        question: str,
        n_documents: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Answer a legal question using the RAG system.

        Args:
            question: The legal question to answer.
            n_documents: Number of documents to retrieve.
            filters: Optional filters for document retrieval.

        Returns:
            Dict containing the answer and supporting information.
        """
        try:
            # Retrieve relevant documents
            search_results = self.vectorization_processor.search_similar_documents(
                query=question,
                n_results=n_documents,
                filters=filters
            )

            # Prepare context from retrieved documents
            context = self._prepare_context(
                documents=[{
                    "document": doc,
                    "metadata": meta
                } for doc, meta in zip(
                    search_results["documents"],
                    search_results["metadatas"], strict=False
                )]
            )

            # Generate answer using LLM
            with get_openai_callback() as cb:
                response = await self.qa_chain.arun(
                    context=context,
                    question=question
                )

                # Prepare response with metadata
                result = {
                    "answer": response,
                    "sources": search_results["metadatas"],
                    "usage": {
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_tokens": cb.total_tokens,
                        "total_cost": cb.total_cost
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                logger.info(f"Generated answer for question: {question[:100]}...")
                return result

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise

    async def analyze_legal_document(
        self,
        document_text: str,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """Analyze a legal document using the RAG system.

        Args:
            document_text: The text of the legal document to analyze.
            analysis_type: Type of analysis to perform ("summary", "key_points", "risks").

        Returns:
            Dict containing the analysis results.
        """
        try:
            # Define analysis prompts
            analysis_prompts = {
                "summary": """請提供以下法律文件的摘要：

                文件內容：
                {document}

                請包含：
                1. 主要內容概述
                2. 關鍵法律論點
                3. 結論或判決結果""",

                "key_points": """請分析以下法律文件的要點：

                文件內容：
                {document}

                請列出：
                1. 主要法律爭議
                2. 適用法條
                3. 關鍵證據
                4. 法院見解""",

                "risks": """請評估以下法律文件可能涉及的風險：

                文件內容：
                {document}

                請分析：
                1. 潛在法律風險
                2. 合規問題
                3. 建議對策"""
            }

            if analysis_type not in analysis_prompts:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")

            # Create analysis prompt
            analysis_template = PromptTemplate(
                input_variables=["document"],
                template=analysis_prompts[analysis_type]
            )

            analysis_chain = LLMChain(
                llm=self.llm,
                prompt=analysis_template
            )

            # Generate analysis
            with get_openai_callback() as cb:
                response = await analysis_chain.arun(document=document_text)

                result = {
                    "analysis": response,
                    "analysis_type": analysis_type,
                    "usage": {
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_tokens": cb.total_tokens,
                        "total_cost": cb.total_cost
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                logger.info(f"Generated {analysis_type} analysis for document")
                return result

        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise
