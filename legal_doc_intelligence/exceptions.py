"""
異常處理模組
"""

class DocumentError(Exception):
    """文件處理相關錯誤"""
    pass

class ValidationError(Exception):
    """驗證相關錯誤"""
    pass

class ProcessingError(Exception):
    """處理過程中的錯誤"""
    pass
