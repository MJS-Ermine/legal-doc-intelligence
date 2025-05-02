from datetime import datetime
from typing import Any, Dict, Generator

import scrapy
from scrapy.http import Request, Response

from ..utils.text_cleaner import clean_text, mask_personal_info


class JudicialSpider(scrapy.Spider):
    """台灣司法判決書爬蟲
    
    負責爬取台灣各級法院的判決書內容，並進行初步的數據清理
    """
    name = "judicial_spider"
    allowed_domains = ["judicial.gov.tw"]
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
    }

    def __init__(self, start_date: str = None, end_date: str = None, *args, **kwargs):
        """初始化爬蟲參數
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
        """
        super(JudicialSpider, self).__init__(*args, **kwargs)
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

    def start_requests(self) -> Generator[Request, None, None]:
        """生成初始請求
        
        根據日期範圍生成對應的搜索請求
        """
        base_url = "https://judgment.judicial.gov.tw/FJUD/default_AD.aspx"
        yield scrapy.Request(
            url=base_url,
            callback=self.parse_search_page,
            meta={'dont_redirect': True, 'handle_httpstatus_list': [302]}
        )

    def parse_search_page(self, response: Response) -> Generator[Request, None, None]:
        """解析搜索頁面，提取判決書列表
        
        Args:
            response: 搜索頁面響應
        """
        # 解析判決書列表頁面
        for link in response.css('table.table_1 tr td a::attr(href)').getall():
            yield response.follow(
                link,
                callback=self.parse_document,
                meta={'dont_redirect': True}
            )

        # 處理分頁
        next_page = response.css('a#hlNext::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_search_page,
                meta={'dont_redirect': True}
            )

    def parse_document(self, response: Response) -> Dict[str, Any]:
        """解析單個判決書詳情頁
        
        Args:
            response: 判決書詳情頁響應
        
        Returns:
            解析後的判決書數據
        """
        # 提取基本信息
        title = response.css('div.text_1::text').get('')
        court = response.css('div.text_1::text').re_first(r'(\w+法院)', '')
        case_number = response.css('div.text_1::text').re_first(r'(\d+年度\w+字第\d+號)', '')

        # 提取判決內容
        content = '\n'.join(response.css('div#jud_content::text').getall())

        # 清理和脫敏
        cleaned_content = clean_text(content)
        masked_content = mask_personal_info(cleaned_content)

        # 提取判決日期
        date_str = response.css('div.text_1::text').re_first(r'中華民國(\d+)年(\d+)月(\d+)日', '')
        if date_str:
            year, month, day = map(int, date_str.split())
            judgment_date = datetime(year + 1911, month, day)  # 民國年轉西元年
        else:
            judgment_date = None

        return {
            'doc_id': f"{court}_{case_number}",
            'title': title,
            'court': court,
            'case_number': case_number,
            'judgment_date': judgment_date,
            'raw_content': content,
            'processed_content': {
                'cleaned': cleaned_content,
                'masked': masked_content
            },
            'metadata': {
                'url': response.url,
                'crawl_time': datetime.utcnow().isoformat()
            }
        }
