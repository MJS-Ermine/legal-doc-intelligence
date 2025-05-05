"""Spider for crawling Taiwan Judicial Yuan's decision database."""

from datetime import datetime
from typing import Any, Generator, Iterator

import scrapy
from loguru import logger
from scrapy.http import Request, Response


class JudicialSpider(scrapy.Spider):
    """Spider for crawling court decisions from the Judicial Yuan website."""

    name = "judicial_spider"
    allowed_domains = ["judicial.gov.tw"]

    # Base URL for the search interface
    start_urls = ["https://judicial.gov.tw/xxx"]  # TODO: 替換為實際入口

    # Custom settings for this spider
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # 2 seconds delay between requests
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'USER_AGENT': 'Legal-Doc-Intelligence-Bot (+https://github.com/yourusername/legal-doc-intelligence)',
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the spider with custom parameters."""
        super().__init__(*args, **kwargs)
        self.court = kwargs.get('court', '')  # e.g., 'TPS' for Taipei District Court
        self.start_date = kwargs.get('start_date', '')  # format: YYYY-MM-DD
        self.end_date = kwargs.get('end_date', '')  # format: YYYY-MM-DD

    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests.

        Yields:
            Request: Initial search form request.
        """
        # 特許繁體中文註釋：處理司法院法學資料檢索系統的初始搜尋請求
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse_search_page,
                dont_filter=True,
                meta={'dont_redirect': True, 'handle_httpstatus_list': [302]}
            )

    def parse_search_page(self, response: Response) -> Generator[Request, None, None]:
        """Parse the search page and submit the search form.

        Args:
            response: Response object from the search page.

        Yields:
            Request: Search result requests.
        """
        # 特許繁體中文註釋：解析搜尋頁面並提交表單
        try:
            # Extract form data and prepare search parameters
            form_data = {
                'court': self.court,
                'date': f'{self.start_date}+至+{self.end_date}',
                # Add other necessary form fields
            }

            # Submit search form
            yield Request(
                url=response.urljoin('search.aspx'),
                method='POST',
                formdata=form_data,
                callback=self.parse_search_results,
                dont_filter=True
            )

        except Exception as e:
            logger.error(f"Error parsing search page: {str(e)}")

    def parse_search_results(self, response: Response) -> Generator[Request, None, None]:
        """Parse the search results page.

        Args:
            response: Response object from the search results.

        Yields:
            Request: Individual decision page requests.
        """
        # 特許繁體中文註釋：解析搜尋結果頁面，提取判決書連結
        try:
            # Extract decision links
            for link in response.css('a.decision-link::attr(href)').getall():
                yield Request(
                    url=response.urljoin(link),
                    callback=self.parse_decision,
                    meta={'dont_redirect': True}
                )

            # Handle pagination
            next_page = response.css('a.next-page::attr(href)').get()
            if next_page:
                yield Request(
                    url=response.urljoin(next_page),
                    callback=self.parse_search_results
                )

        except Exception as e:
            logger.error(f"Error parsing search results: {str(e)}")

    def parse_decision(self, response: Response) -> dict[str, Any]:
        """Parse individual decision page.

        Args:
            response: Response object from the decision page.

        Returns:
            dict: Extracted decision data.
        """
        # 特許繁體中文註釋：解析個別判決書頁面，提取所需資訊
        try:
            # Extract decision content
            title = response.css('h1::text').get('')
            content = response.css('div.decision-content::text').getall()
            decision_date_str = response.css('span.decision-date::text').get('')

            # Parse decision date
            decision_date = None
            if decision_date_str:
                try:
                    decision_date = datetime.strptime(decision_date_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Could not parse decision date: {decision_date_str}")

            # Return extracted data
            return {
                'title': title.strip(),
                'content': '\n'.join(content).strip(),
                'source_url': response.url,
                'decision_date': decision_date,
                'court_name': self.court,
                'crawled_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error parsing decision page {response.url}: {str(e)}")
            return {}

    def parse(self, response: scrapy.http.Response) -> Iterator[Any]:
        """解析列表頁，提取標題與內文連結，處理分頁。"""
        # TODO: 補充選擇器
        for item in response.css(".doc-item"):
            yield {
                "title": item.css(".title::text").get(),
                "url": response.urljoin(item.css("a::attr(href)").get()),
            }
        # 處理分頁
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def handle_error(self, failure: Any) -> None:
        self.logger.error(f"Request failed: {failure}")
