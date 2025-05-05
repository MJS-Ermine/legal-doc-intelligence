"""
進階使用示例：展示法律文件智能處理平台的高級功能
"""
from typing import Any, Dict, List

from legal_doc_intelligence.analysis import TextAnalyzer
from legal_doc_intelligence.context import ContextManager
from legal_doc_intelligence.document import Document
from legal_doc_intelligence.processor import LegalDocProcessor
from legal_doc_intelligence.utils.logger import setup_logger

logger = setup_logger(__name__)

def analyze_multiple_documents(file_paths: List[str]) -> Dict[str, Any]:
    """
    分析多個法律文件並生成綜合報告

    Args:
        file_paths: 文件路徑列表

    Returns:
        Dict[str, Any]: 分析報告
    """
    # 初始化處理器和上下文管理器
    processor = LegalDocProcessor()
    context = ContextManager()
    analyzer = TextAnalyzer()

    # 處理所有文件
    documents = []
    for path in file_paths:
        try:
            doc = Document.from_file(path)
            processed_doc = processor.process(doc)
            documents.append(processed_doc)
            context.add_document(processed_doc)
        except Exception as e:
            logger.error(f"處理文件 {path} 時發生錯誤: {e}")

    # 生成綜合報告
    report = {
        "total_documents": len(documents),
        "entities": analyzer.extract_common_entities(documents),
        "citations": analyzer.extract_common_citations(documents),
        "timeline": analyzer.create_merged_timeline(documents),
        "document_clusters": analyzer.cluster_documents(documents),
        "key_concepts": analyzer.extract_key_concepts(documents)
    }

    return report

def main():
    # 示例文件列表
    files = [
        "examples/case1.txt",
        "examples/case2.txt",
        "examples/contract1.txt"
    ]

    # 分析文件
    report = analyze_multiple_documents(files)

    # 輸出報告
    print("\n=== 分析報告 ===")
    print(f"處理文件總數: {report['total_documents']}")

    print("\n共同實體:")
    for entity_type, entities in report['entities'].items():
        print(f"{entity_type}: {', '.join(entities)}")

    print("\n引用分析:")
    for citation in report['citations']:
        print(f"- {citation}")

    print("\n時間軸:")
    for event in report['timeline']:
        print(f"- {event['date']}: {event['description']}")

    print("\n文件聚類:")
    for cluster_id, docs in report['document_clusters'].items():
        print(f"\n群集 {cluster_id}:")
        for doc in docs:
            print(f"- {doc.title}")

    print("\n關鍵概念:")
    for concept, frequency in report['key_concepts'].items():
        print(f"- {concept}: {frequency}")

if __name__ == "__main__":
    main()
