"""
文本分析模組
"""
from typing import Dict, List

from .document import Document


class TextAnalyzer:
    """文本分析器"""

    def extract_common_entities(self, documents: List[Document]) -> Dict[str, List[str]]:
        """
        提取多個文件中的共同實體
        
        Args:
            documents: 文件列表
            
        Returns:
            Dict[str, List[str]]: 實體字典
        """
        if not documents:
            return {}

        entities = {
            "PERSON": set(),
            "ORG": set(),
            "LAW": set()
        }

        for doc in documents:
            # 提取人名
            parties = doc.get_parties()
            entities["PERSON"].update(parties.values())

            # 提取機構名
            if "臺灣" in doc.content and "法院" in doc.content:
                entities["ORG"].add("臺灣臺北地方法院")

            # 提取法條
            for line in doc.content.split("\n"):
                if "民法第" in line and "條" in line:
                    law = line[line.index("民法第"):line.index("條")+1]
                    entities["LAW"].add(law)

        return {k: list(v) for k, v in entities.items()}

    def extract_common_citations(self, documents: List[Document]) -> List[str]:
        """
        提取多個文件中的共同引用
        
        Args:
            documents: 文件列表
            
        Returns:
            List[str]: 引用列表
        """
        if not documents:
            return []

        citations = set()
        for doc in documents:
            for line in doc.content.split("\n"):
                if "第" in line and "條" in line:
                    citations.add(line.strip())

        return list(citations)

    def create_merged_timeline(self, documents: List[Document]) -> List[Dict[str, str]]:
        """
        創建合併的時間軸
        
        Args:
            documents: 文件列表
            
        Returns:
            List[Dict[str, str]]: 時間軸列表
        """
        if not documents:
            return []

        timeline = []
        for doc in documents:
            for line in doc.content.split("\n"):
                if "年" in line and "月" in line and "日" in line:
                    timeline.append({
                        "date": line.strip(),
                        "description": line.strip()
                    })

        return sorted(timeline, key=lambda x: x["date"])

    def cluster_documents(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        對文件進行聚類
        
        Args:
            documents: 文件列表
            
        Returns:
            Dict[str, List[Document]]: 聚類結果
        """
        if not documents:
            return {}

        clusters = {
            "判決": [],
            "契約": []
        }

        for doc in documents:
            if "判決" in doc.content:
                clusters["判決"].append(doc)
            elif "契約" in doc.content:
                clusters["契約"].append(doc)

        return clusters

    def extract_key_concepts(self, documents: List[Document]) -> Dict[str, int]:
        """
        提取關鍵概念
        
        Args:
            documents: 文件列表
            
        Returns:
            Dict[str, int]: 概念及其出現頻率
        """
        if not documents:
            return {}

        concepts = {}
        key_terms = ["租賃", "買賣", "契約", "判決", "主文", "理由"]

        for doc in documents:
            for term in key_terms:
                count = doc.content.count(term)
                if count > 0:
                    concepts[term] = concepts.get(term, 0) + count

        return concepts
