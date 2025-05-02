法律文件智能處理平台
==================

歡迎使用法律文件智能處理平台的文檔！

.. toctree::
   :maxdepth: 2
   :caption: 目錄:

   installation
   quickstart
   api
   examples
   contributing
   changelog

快速入門
--------

安裝套件::

    pip install legal-doc-intelligence

基本使用::

    from legal_doc_intelligence.document import Document
    from legal_doc_intelligence.processor import LegalDocProcessor

    # 創建文件對象
    doc = Document.from_file("sample.txt")
    
    # 初始化處理器
    processor = LegalDocProcessor()
    
    # 處理文件
    processed_doc = processor.process(doc)

功能特點
--------

* 支援多種法律文件格式
* 智能文本分析
* 實體識別
* 引用檢測
* 時間軸生成
* 相似案例查詢

貢獻指南
--------

我們歡迎各種形式的貢獻，包括但不限於：

* 錯誤報告
* 功能請求
* 文檔改進
* 代碼貢獻

詳細資訊請參考 :doc:`contributing` 頁面。 