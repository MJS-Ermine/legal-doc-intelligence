"""Evaluation framework for the Legal Document Intelligence Platform."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger
from nltk.translate.bleu_score import sentence_bleu
from rouge_chinese import Rouge
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class LegalEvaluator:
    """Evaluator for assessing the quality of legal document processing and RAG responses."""

    def __init__(
        self,
        embedding_model: Optional[str] = "paraphrase-multilingual-mpnet-base-v2"
    ) -> None:
        """Initialize the evaluator.

        Args:
            embedding_model: Name of the sentence transformer model for semantic similarity.
        """
        self.rouge = Rouge()
        self.embedding_model = SentenceTransformer(embedding_model)

        logger.info("Initialized Legal Evaluator")

    def evaluate_rag_response(
        self,
        question: str,
        response: str,
        ground_truth: str,
        retrieved_docs: List[str]
    ) -> Dict[str, Any]:
        """Evaluate a RAG system response.

        Args:
            question: Original question.
            response: Generated response.
            ground_truth: Ground truth answer.
            retrieved_docs: List of retrieved documents.

        Returns:
            Evaluation metrics.
        """
        try:
            # 計算 ROUGE 分數
            rouge_scores = self.rouge.get_scores(response, ground_truth)[0]

            # 計算 BLEU 分數
            bleu_score = sentence_bleu(
                [list(ground_truth)],
                list(response),
                weights=(0.25, 0.25, 0.25, 0.25)
            )

            # 計算語義相似度
            response_embedding = self.embedding_model.encode([response])[0]
            truth_embedding = self.embedding_model.encode([ground_truth])[0]
            semantic_similarity = cosine_similarity(
                [response_embedding],
                [truth_embedding]
            )[0][0]

            # 評估檢索相關性
            retrieval_scores = self._evaluate_retrieval(
                question=question,
                retrieved_docs=retrieved_docs
            )

            # 組合評估結果
            evaluation = {
                "rouge_scores": {
                    "rouge-1": {
                        "f": rouge_scores["rouge-1"]["f"],
                        "p": rouge_scores["rouge-1"]["p"],
                        "r": rouge_scores["rouge-1"]["r"]
                    },
                    "rouge-2": {
                        "f": rouge_scores["rouge-2"]["f"],
                        "p": rouge_scores["rouge-2"]["p"],
                        "r": rouge_scores["rouge-2"]["r"]
                    },
                    "rouge-l": {
                        "f": rouge_scores["rouge-l"]["f"],
                        "p": rouge_scores["rouge-l"]["p"],
                        "r": rouge_scores["rouge-l"]["r"]
                    }
                },
                "bleu_score": bleu_score,
                "semantic_similarity": float(semantic_similarity),
                "retrieval_evaluation": retrieval_scores,
                "timestamp": datetime.utcnow().isoformat()
            }

            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating RAG response: {str(e)}")
            raise

    def _evaluate_retrieval(
        self,
        question: str,
        retrieved_docs: List[str]
    ) -> Dict[str, float]:
        """Evaluate the quality of retrieved documents.

        Args:
            question: Original question.
            retrieved_docs: List of retrieved documents.

        Returns:
            Retrieval quality metrics.
        """
        try:
            # 計算問題與檢索文檔的相似度
            question_embedding = self.embedding_model.encode([question])[0]
            doc_embeddings = self.embedding_model.encode(retrieved_docs)

            similarities = cosine_similarity(
                [question_embedding],
                doc_embeddings
            )[0]

            return {
                "max_similarity": float(np.max(similarities)),
                "mean_similarity": float(np.mean(similarities)),
                "min_similarity": float(np.min(similarities))
            }

        except Exception as e:
            logger.error(f"Error evaluating retrieval: {str(e)}")
            raise

    def evaluate_entity_extraction(
        self,
        extracted_entities: Dict[str, List[str]],
        ground_truth_entities: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate named entity extraction performance.

        Args:
            extracted_entities: Dictionary of extracted entities.
            ground_truth_entities: Dictionary of ground truth entities.

        Returns:
            Entity extraction metrics per entity type.
        """
        try:
            results = {}

            for entity_type in ground_truth_entities:
                if entity_type not in extracted_entities:
                    results[entity_type] = {
                        "precision": 0.0,
                        "recall": 0.0,
                        "f1": 0.0
                    }
                    continue

                extracted = set(extracted_entities[entity_type])
                truth = set(ground_truth_entities[entity_type])

                true_positives = len(extracted.intersection(truth))
                false_positives = len(extracted - truth)
                false_negatives = len(truth - extracted)

                precision = (
                    true_positives / (true_positives + false_positives)
                    if (true_positives + false_positives) > 0 else 0
                )
                recall = (
                    true_positives / (true_positives + false_negatives)
                    if (true_positives + false_negatives) > 0 else 0
                )
                f1 = (
                    (precision * recall) / (precision + recall)
                    if (precision + recall) > 0 else 0
                )

                results[entity_type] = {
                    "precision": precision,
                    "recall": recall,
                    "f1": f1
                }

            return results

        except Exception as e:
            logger.error(f"Error evaluating entity extraction: {str(e)}")
            raise

    def evaluate_document_segmentation(
        self,
        segmented_doc: List[Dict[str, Any]],
        ground_truth_segments: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate document segmentation quality.

        Args:
            segmented_doc: List of document segments.
            ground_truth_segments: List of ground truth segments.

        Returns:
            Segmentation quality metrics.
        """
        try:
            # 計算段落類型的準確率
            correct_types = 0
            total_segments = len(ground_truth_segments)

            if len(segmented_doc) != total_segments:
                logger.warning(f"Segment count mismatch: {len(segmented_doc)} vs {total_segments}")

            for pred, truth in zip(segmented_doc, ground_truth_segments, strict=False):
                if pred["type"] == truth["type"]:
                    correct_types += 1

            type_accuracy = correct_types / total_segments if total_segments > 0 else 0

            # 計算內容相似度
            content_similarities = []
            for pred, truth in zip(segmented_doc, ground_truth_segments, strict=False):
                pred_embedding = self.embedding_model.encode([pred["content"]])[0]
                truth_embedding = self.embedding_model.encode([truth["content"]])[0]
                similarity = cosine_similarity([pred_embedding], [truth_embedding])[0][0]
                content_similarities.append(similarity)

            return {
                "type_accuracy": type_accuracy,
                "content_similarity_mean": float(np.mean(content_similarities)),
                "content_similarity_std": float(np.std(content_similarities))
            }

        except Exception as e:
            logger.error(f"Error evaluating document segmentation: {str(e)}")
            raise
