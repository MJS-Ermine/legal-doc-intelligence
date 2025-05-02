"""Text processor for legal documents."""

import re
from typing import Any, Dict, List

import jieba
import jieba.posseg as pseg
from loguru import logger


class LegalTextProcessor:
    """Processor for legal text preprocessing and standardization."""

    def __init__(self) -> None:
        """Initialize the legal text processor."""
        # 載入自定義詞典
        self._load_custom_dictionary()

        # 定義正則表達式模式
        self.patterns = {
            "case_number": r"[\u4e00-\u9fff]{2,4}(?:重上|重訴|上訴|訴|附|簡|要|選|矚|速)?字第\d+號",
            "date": r"中華民國\d+年\d+月\d+日|民國\d+年\d+月\d+日|\d{4}年\d{1,2}月\d{1,2}日",
            "law_reference": r"依據?(?:《|【|「)?[\u4e00-\u9fff]{2,10}(?:》|】|」)?第[\d零一二三四五六七八九十百千]+條(?:第[\d零一二三四五六七八九十百千]+項)?(?:第[\d零一二三四五六七八九十百千]+款)?",
            "court_level": r"[高地]等法院|最高法院|最高行政法院|智慧財產法院"
        }

    def _load_custom_dictionary(self) -> None:
        """Load custom legal dictionary for jieba."""
        try:
            # 添加法律專業詞彙
            custom_words = [
                ("原告", "n"), ("被告", "n"), ("上訴人", "n"), ("被上訴人", "n"),
                ("聲請人", "n"), ("相對人", "n"), ("代理人", "n"), ("訴訟代理人", "n"),
                ("判決", "n"), ("裁定", "n"), ("民事", "n"), ("刑事", "n"),
                ("行政訴訟", "n"), ("假扣押", "n"), ("假處分", "n"), ("強制執行", "n")
            ]

            for word, pos in custom_words:
                jieba.add_word(word, tag=pos)

            logger.info("Loaded custom legal dictionary")

        except Exception as e:
            logger.error(f"Error loading custom dictionary: {str(e)}")
            raise

    def clean_text(self, text: str) -> str:
        """Clean and normalize legal text.
        
        Args:
            text: Raw legal text.
            
        Returns:
            Cleaned and normalized text.
        """
        try:
            # 移除多餘的空白和換行
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)

            # 統一標點符號
            text = text.replace('；', ';').replace('，', ',')
            text = text.replace('。', '.').replace('、', ',')

            # 統一數字格式
            text = re.sub(r'[零一二三四五六七八九十百千萬億]+',
                         lambda x: str(self._chinese_to_number(x.group())),
                         text)

            return text.strip()

        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            raise

    def _chinese_to_number(self, chinese_num: str) -> int:
        """Convert Chinese numerals to Arabic numbers.
        
        Args:
            chinese_num: Chinese numeral string.
            
        Returns:
            Converted integer.
        """
        num_dict = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
            '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '十': 10, '百': 100, '千': 1000, '萬': 10000, '億': 100000000
        }

        if chinese_num.isdigit():
            return int(chinese_num)

        result = 0
        tmp = 0
        for char in chinese_num:
            curr = num_dict.get(char, 0)
            if curr >= 10:
                result += tmp * curr
                tmp = 0
            else:
                tmp = curr
        result += tmp
        return result if result > 0 else tmp

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from legal text.
        
        Args:
            text: Legal document text.
            
        Returns:
            Dictionary containing extracted metadata.
        """
        try:
            metadata = {}

            # 提取案號
            case_numbers = re.findall(self.patterns["case_number"], text)
            if case_numbers:
                metadata["case_number"] = case_numbers[0]

            # 提取日期
            dates = re.findall(self.patterns["date"], text)
            if dates:
                metadata["document_date"] = dates[0]

            # 提取法院層級
            court_levels = re.findall(self.patterns["court_level"], text)
            if court_levels:
                metadata["court_level"] = court_levels[0]

            # 提取法條引用
            law_refs = re.findall(self.patterns["law_reference"], text)
            if law_refs:
                metadata["law_references"] = law_refs

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise

    def segment_document(self, text: str) -> List[Dict[str, Any]]:
        """Segment document into logical parts.
        
        Args:
            text: Legal document text.
            
        Returns:
            List of document segments with their types.
        """
        try:
            segments = []
            current_segment = []
            current_type = None

            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 判斷段落類型
                if re.match(r'^主\s*文', line):
                    if current_segment:
                        segments.append({
                            "type": current_type,
                            "content": '\n'.join(current_segment)
                        })
                    current_type = "main_text"
                    current_segment = []
                elif re.match(r'^事\s*實', line):
                    if current_segment:
                        segments.append({
                            "type": current_type,
                            "content": '\n'.join(current_segment)
                        })
                    current_type = "facts"
                    current_segment = []
                elif re.match(r'^理\s*由', line):
                    if current_segment:
                        segments.append({
                            "type": current_type,
                            "content": '\n'.join(current_segment)
                        })
                    current_type = "reasoning"
                    current_segment = []
                else:
                    current_segment.append(line)

            # 添加最後一個段落
            if current_segment and current_type:
                segments.append({
                    "type": current_type,
                    "content": '\n'.join(current_segment)
                })

            return segments

        except Exception as e:
            logger.error(f"Error segmenting document: {str(e)}")
            raise

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from legal text.
        
        Args:
            text: Legal text to process.
            
        Returns:
            Dictionary of entity types and their values.
        """
        try:
            entities = {
                "person": [],
                "organization": [],
                "location": [],
                "law": [],
                "date": []
            }

            # 使用 jieba 詞性標注
            words = pseg.cut(text)

            for word, flag in words:
                if flag == 'nr':  # 人名
                    entities["person"].append(word)
                elif flag == 'nt':  # 機構名
                    entities["organization"].append(word)
                elif flag == 'ns':  # 地名
                    entities["location"].append(word)

            # 提取法條引用
            law_refs = re.findall(self.patterns["law_reference"], text)
            entities["law"] = law_refs

            # 提取日期
            dates = re.findall(self.patterns["date"], text)
            entities["date"] = dates

            # 去重
            for entity_type in entities:
                entities[entity_type] = list(set(entities[entity_type]))

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise

class TextProcessor:
    """文本處理器，負責清理、分詞、個資遮蔽等。"""

    @staticmethod
    def clean_html(text: str) -> str:
        """去除 HTML 標籤與多餘空白。

        Args:
            text (str): 原始文本
        Returns:
            str: 清理後文本
        """
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def remove_special_chars(text: str) -> str:
        """去除特殊字元。

        Args:
            text (str): 原始文本
        Returns:
            str: 處理後文本
        """
        return re.sub(r"[^\w\u4e00-\u9fff ]", "", text)

    @staticmethod
    def mask_personal_info(text: str) -> str:
        """遮蔽個資（如身分證、電話、email）。

        Args:
            text (str): 原始文本
        Returns:
            str: 遮蔽後文本
        """
        # TODO: 補充遮蔽規則
        return text

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """簡易分詞。

        Args:
            text (str): 文本
        Returns:
            List[str]: 分詞結果
        """
        return text.split()
