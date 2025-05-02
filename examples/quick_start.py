"""
快速入門示例：展示如何使用法律文件智能處理平台的基本功能
"""
from legal_doc_intelligence.context import ContextManager
from legal_doc_intelligence.document import Document
from legal_doc_intelligence.processor import LegalDocProcessor
from legal_doc_intelligence.validation import ValidationRules


def main():
    # 1. 創建文件對象
    doc = Document.from_file("examples/sample.txt")

    # 2. 初始化處理器
    processor = LegalDocProcessor()

    # 3. 設置驗證規則
    rules = ValidationRules()
    rules.add_format_rule("must_have_date", "文件必須包含日期")
    rules.add_content_rule("must_have_parties", "文件必須包含當事人信息")

    # 4. 驗證文件
    validation_result = processor.validate(doc, rules)
    print("驗證結果:", validation_result.to_dict())

    # 5. 處理文件
    processed_doc = processor.process(doc)

    # 6. 提取關鍵信息
    entities = processed_doc.get_entities()
    print("識別到的實體:", entities)

    citations = processed_doc.get_citations()
    print("識別到的引用:", citations)

    timeline = processed_doc.get_timeline()
    print("事件時間線:", timeline)

    # 7. 使用上下文管理
    context = ContextManager()
    context.add_document(processed_doc)

    # 8. 相似案例查詢
    similar_cases = context.find_similar_cases(processed_doc, top_k=3)
    print("相似案例:", similar_cases)

if __name__ == "__main__":
    main()
