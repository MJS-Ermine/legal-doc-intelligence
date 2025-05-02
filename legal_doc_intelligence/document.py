"""
文件處理模組
"""
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import DocumentError


class Document:
    """文件類，用於處理和分析法律文件"""

    def __init__(self, content: str, file_path: Optional[Path] = None):
        """
        初始化文件對象
        
        Args:
            content: 文件內容
            file_path: 文件路徑
        """
        self.content = content
        self.file_path = file_path
        self._parse_metadata()

    @classmethod
    def from_file(cls, file_path: str) -> "Document":
        """
        從文件創建文件對象
        
        Args:
            file_path: 文件路徑
            
        Returns:
            Document: 文件對象
            
        Raises:
            DocumentError: 當文件不存在或為空時
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentError(f"文件不存在：{file_path}")

        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise DocumentError(f"文件為空：{file_path}")

        return cls(content, path)

    def _parse_metadata(self):
        """解析文件元數據"""
        lines = self.content.split("\n")
        self.title = lines[0].strip() if lines else ""
        self.case_number = lines[1].strip() if len(lines) > 1 else ""

        # 解析日期
        for line in lines:
            if "中華民國" in line and "年" in line:
                self.date = line.strip()
                break
        else:
            self.date = ""

    def get_parties(self) -> Dict[str, str]:
        """
        獲取當事人信息
        
        Returns:
            Dict[str, str]: 當事人信息字典
        """
        parties = {}
        lines = self.content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("原告"):
                parties["原告"] = line.replace("原告", "").strip()
            elif line.startswith("被告"):
                parties["被告"] = line.replace("被告", "").strip()
        return parties

    def get_sections(self) -> Dict[str, str]:
        """
        獲取文件段落
        
        Returns:
            Dict[str, str]: 段落字典
        """
        sections = {}
        current_section = None
        current_content = []

        for line in self.content.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line in ["主文", "事實及理由"] or line.startswith("第") and "條" in line:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def get_paragraphs(self) -> List[str]:
        """
        獲取文件段落列表
        
        Returns:
            List[str]: 段落列表
        """
        return [p.strip() for p in self.content.split("\n\n") if p.strip()]

    def extract_keywords(self) -> List[str]:
        """
        提取關鍵詞
        
        Returns:
            List[str]: 關鍵詞列表
        """
        # 簡單實現，實際應使用更複雜的算法
        keywords = []
        for line in self.content.split("\n"):
            if "法" in line or "條" in line:
                keywords.append(line.strip())
        return keywords

    def get_cleaned_text(self) -> str:
        """
        獲取清理後的文本
        
        Returns:
            str: 清理後的文本
        """
        lines = [line.strip() for line in self.content.split("\n")]
        return "\n".join(line for line in lines if line)

    def calculate_similarity(self, other: "Document") -> float:
        """
        計算與另一個文件的相似度
        
        Args:
            other: 另一個文件對象
            
        Returns:
            float: 相似度分數
        """
        # 簡單實現，實際應使用更複雜的算法
        common_words = set(self.content.split()) & set(other.content.split())
        total_words = set(self.content.split()) | set(other.content.split())
        return len(common_words) / len(total_words) if total_words else 0.0

    def compare_with(self, other: "Document") -> Dict[str, List[str]]:
        """
        與另一個文件比較差異
        
        Args:
            other: 另一個文件對象
            
        Returns:
            Dict[str, List[str]]: 差異信息
        """
        self_lines = set(self.content.split("\n"))
        other_lines = set(other.content.split("\n"))

        return {
            "additions": list(other_lines - self_lines),
            "deletions": list(self_lines - other_lines)
        }
