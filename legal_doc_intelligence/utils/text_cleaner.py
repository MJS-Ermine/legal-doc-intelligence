import logging
import re
from typing import Any, Dict, List

import jieba

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """清理文本內容

    Args:
        text: 原始文本

    Returns:
        清理後的文本
    """
    if not text:
        return ""

    # 移除多餘空白
    text = re.sub(r'\s+', ' ', text.strip())

    # 統一全形/半形符號
    text = text.translate(str.maketrans('，。！？；：「」『』（）', ',.!?;:""\'\'\\(\\)'))

    # 移除特殊控制字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    return text

def mask_personal_info(text: str) -> str:
    """對文本中的個人信息進行脫敏

    Args:
        text: 原始文本

    Returns:
        脫敏後的文本
    """
    if not text:
        return ""

    # 脫敏身份證字號
    text = re.sub(r'[A-Z]\d{9}', '[身份證號]', text)

    # 脫敏電話號碼
    text = re.sub(r'0\d{1,3}[-\s]?\d{6,8}', '[電話號碼]', text)

    # 脫敏地址
    text = re.sub(r'[台臺][北中南東][市縣].{2,20}[路街巷弄號樓]', '[地址]', text)

    # 脫敏姓名（通過結巴分詞識別人名）
    words = jieba.cut(text)
    for word in words:
        if len(word) >= 2 and jieba.posseg.cut(word).__next__().flag == 'nr':
            text = text.replace(word, '[姓名]')

    return text

def extract_citations(text: str) -> List[Dict[str, Any]]:
    """提取引用法條

    Args:
        text: 原始文本

    Returns:
        引用法條列表
    """
    citations = []

    # 匹配常見法規引用模式
    patterns = [
        r'([\u4e00-\u9fa5]+法)第(\d+)條(?:第(\d+)項)?(?:第(\d+)款)?',
        r'([\u4e00-\u9fa5]+條例)第(\d+)條(?:第(\d+)項)?(?:第(\d+)款)?'
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            citation = {
                'law_name': match.group(1),
                'article': f"第{match.group(2)}條",
                'paragraph': f"第{match.group(3)}項" if match.group(3) else None,
                'subparagraph': f"第{match.group(4)}款" if match.group(4) else None
            }
            citations.append(citation)

    return citations

def segment_document(text: str) -> Dict[str, Any]:
    """將判決書分段

    Args:
        text: 原始文本

    Returns:
        分段後的文本結構
    """
    segments = {
        'main_text': '',
        'fact': '',
        'reason': '',
        'holding': ''
    }

    # 主文段落
    main_text_match = re.search(r'主\s*文\n*(.*?)(?=事\s*實|理\s*由|$)', text, re.DOTALL)
    if main_text_match:
        segments['main_text'] = clean_text(main_text_match.group(1))

    # 事實段落
    fact_match = re.search(r'事\s*實\n*(.*?)(?=理\s*由|$)', text, re.DOTALL)
    if fact_match:
        segments['fact'] = clean_text(fact_match.group(1))

    # 理由段落
    reason_match = re.search(r'理\s*由\n*(.*?)(?=主\s*文|$)', text, re.DOTALL)
    if reason_match:
        segments['reason'] = clean_text(reason_match.group(1))

    # 判決段落
    holding_match = re.search(r'判\s*決\n*(.*?)$', text, re.DOTALL)
    if holding_match:
        segments['holding'] = clean_text(holding_match.group(1))

    return segments
