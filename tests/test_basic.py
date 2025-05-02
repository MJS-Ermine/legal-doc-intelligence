"""Basic unit tests for the Legal Document Intelligence Platform."""


def test_chinese_to_number():
    """Test Chinese number conversion."""
    from legal_doc_intelligence.processors.text_processor import LegalTextProcessor

    processor = LegalTextProcessor()

    # 測試基本數字轉換
    assert processor._chinese_to_number("零") == 0
    assert processor._chinese_to_number("一") == 1
    assert processor._chinese_to_number("十") == 10
    assert processor._chinese_to_number("二十") == 20
    assert processor._chinese_to_number("一百") == 100

    # 測試複雜數字
    assert processor._chinese_to_number("一百二十三") == 123
    assert processor._chinese_to_number("一千零一") == 1001

    # 測試阿拉伯數字
    assert processor._chinese_to_number("123") == 123

def test_clean_text():
    """Test text cleaning functionality."""
    from legal_doc_intelligence.processors.text_processor import LegalTextProcessor

    processor = LegalTextProcessor()

    # 測試空白處理
    text = "這是  一個   測試。"
    assert processor.clean_text(text) == "這是 一個 測試."

    # 測試標點符號統一
    text = "這是，一個；測試。"
    assert processor.clean_text(text) == "這是,一個;測試."

    # 測試數字轉換
    text = "一百二十三"
    assert "123" in processor.clean_text(text)

def test_extract_metadata():
    """Test metadata extraction."""
    from legal_doc_intelligence.processors.text_processor import LegalTextProcessor

    processor = LegalTextProcessor()

    # 測試案號提取
    text = """臺灣臺北地方法院民事判決
    110年度訴字第123號
    原告 張三
    被告 李四"""

    metadata = processor.extract_metadata(text)
    assert "case_number" in metadata
    assert "110年度訴字第123號" in metadata["case_number"]

    # 測試法院層級提取
    assert "court_level" in metadata
    assert "地方法院" in metadata["court_level"]

def test_extract_entities():
    """Test entity extraction."""
    from legal_doc_intelligence.processors.text_processor import LegalTextProcessor

    processor = LegalTextProcessor()

    text = """臺灣臺北地方法院民事判決
    原告 張三
    被告 李四
    上訴人 王五
    代理人 趙六
    民法第一百五十三條"""

    entities = processor.extract_entities(text)

    # 測試人名提取
    assert "person" in entities
    assert "張三" in entities["person"]
    assert "李四" in entities["person"]

    # 測試機構名提取
    assert "organization" in entities
    assert "臺灣臺北地方法院" in entities["organization"]

    # 測試法條提取
    assert "law" in entities
    assert "民法第一百五十三條" in entities["law"]
