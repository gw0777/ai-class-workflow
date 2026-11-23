import axios, { AxiosInstance } from 'axios';
import * as cheerio from 'cheerio';
import puppeteer, { Browser, Page } from 'puppeteer';
import { CrawlJob, CrawlResult } from '../../models/types';

/**
 * 범용 웹 크롤러 베이스 클래스
 * - 정적 페이지: axios + cheerio
 * - 동적 페이지: puppeteer
 * - 주제별 어댑터 패턴으로 확장
 */
export abstract class BaseCrawler {
  protected axiosClient: AxiosInstance;
  protected browser: Browser | null = null;
  protected userAgent: string;
  protected delayMs: number;
  protected timeout: number;

  constructor() {
    this.userAgent =
      process.env.CRAWLER_USER_AGENT ||
      'Universal-Policy-Analysis-Bot/1.0';
    this.delayMs = parseInt(process.env.CRAWLER_DELAY_MS || '1000');
    this.timeout = parseInt(process.env.CRAWLER_TIMEOUT_MS || '30000');

    this.axiosClient = axios.create({
      timeout: this.timeout,
      headers: {
        'User-Agent': this.userAgent,
        Accept:
          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
      },
    });
  }

  /**
   * 정적 페이지 크롤링 (axios + cheerio)
   */
  async crawlStatic(url: string): Promise<CrawlResult> {
    try {
      console.log(`[Crawler] 정적 크롤링 시작: ${url}`);

      const response = await this.axiosClient.get(url);
      const $ = cheerio.load(response.data);

      const result = await this.parseStaticPage($, url);

      await this.delay();
      return result;
    } catch (error) {
      console.error(`[Crawler] 정적 크롤링 실패: ${url}`, error);
      return {
        url,
        title: '',
        content: '',
        metadata: {},
        links: [],
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * 동적 페이지 크롤링 (puppeteer)
   */
  async crawlDynamic(url: string): Promise<CrawlResult> {
    try {
      console.log(`[Crawler] 동적 크롤링 시작: ${url}`);

      if (!this.browser) {
        await this.initBrowser();
      }

      const page = await this.browser!.newPage();
      await page.setUserAgent(this.userAgent);
      await page.setViewport({ width: 1920, height: 1080 });

      await page.goto(url, {
        waitUntil: 'networkidle0',
        timeout: this.timeout,
      });

      // 동적 콘텐츠 로딩 대기
      await this.waitForDynamicContent(page);

      const html = await page.content();
      const $ = cheerio.load(html);

      const result = await this.parseDynamicPage($, page, url);

      await page.close();
      await this.delay();

      return result;
    } catch (error) {
      console.error(`[Crawler] 동적 크롤링 실패: ${url}`, error);
      return {
        url,
        title: '',
        content: '',
        metadata: {},
        links: [],
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * 브라우저 초기화
   */
  protected async initBrowser(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
      ],
    });
    console.log('[Crawler] Puppeteer 브라우저 초기화 완료');
  }

  /**
   * 브라우저 종료
   */
  async closeBrowser(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      console.log('[Crawler] Puppeteer 브라우저 종료');
    }
  }

  /**
   * 지연 (Rate Limiting)
   */
  protected async delay(): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, this.delayMs));
  }

  /**
   * 동적 콘텐츠 로딩 대기 (하위 클래스에서 오버라이드)
   */
  protected async waitForDynamicContent(page: Page): Promise<void> {
    // 기본 구현: 1초 대기
    await page.waitForTimeout(1000);
  }

  /**
   * 정적 페이지 파싱 (하위 클래스에서 구현)
   */
  protected abstract parseStaticPage(
    $: cheerio.Root,
    url: string
  ): Promise<CrawlResult>;

  /**
   * 동적 페이지 파싱 (하위 클래스에서 구현)
   */
  protected abstract parseDynamicPage(
    $: cheerio.Root,
    page: Page,
    url: string
  ): Promise<CrawlResult>;

  /**
   * 링크 추출 (상대 경로 -> 절대 경로 변환)
   */
  protected extractLinks(
    $: cheerio.Root,
    baseUrl: string,
    selector: string = 'a'
  ): string[] {
    const links: string[] = [];
    const url = new URL(baseUrl);

    $(selector).each((_, element) => {
      const href = $(element).attr('href');
      if (href) {
        try {
          // 절대 URL 변환
          const absoluteUrl = new URL(href, baseUrl);
          // 같은 도메인만 수집
          if (absoluteUrl.hostname === url.hostname) {
            links.push(absoluteUrl.href);
          }
        } catch (e) {
          // 잘못된 URL 무시
        }
      }
    });

    return [...new Set(links)]; // 중복 제거
  }

  /**
   * 텍스트 정리
   */
  protected cleanText(text: string): string {
    return text
      .replace(/\s+/g, ' ') // 공백 정규화
      .replace(/\n+/g, '\n') // 줄바꿈 정규화
      .trim();
  }

  /**
   * 메타데이터 추출
   */
  protected extractMetadata($: cheerio.Root): Record<string, any> {
    const metadata: Record<string, any> = {};

    // Open Graph 태그
    $('meta[property^="og:"]').each((_, element) => {
      const property = $(element).attr('property');
      const content = $(element).attr('content');
      if (property && content) {
        const key = property.replace('og:', '');
        metadata[key] = content;
      }
    });

    // 일반 메타 태그
    $('meta[name]').each((_, element) => {
      const name = $(element).attr('name');
      const content = $(element).attr('content');
      if (name && content) {
        metadata[name] = content;
      }
    });

    return metadata;
  }

  /**
   * 날짜 추출 및 파싱
   */
  protected parseDate(dateString: string): Date | undefined {
    try {
      const date = new Date(dateString);
      return isNaN(date.getTime()) ? undefined : date;
    } catch {
      return undefined;
    }
  }
}

/**
 * 범용 정책 문서 크롤러
 * - 템플릿 메서드 패턴으로 확장 가능
 */
export class GenericPolicyCrawler extends BaseCrawler {
  private selectors: Record<string, string>;

  constructor(selectors?: Record<string, string>) {
    super();
    this.selectors = selectors || {
      title: 'h1, h2.title, .document-title',
      content: 'article, .content, .document-content, main',
      date: '.publish-date, .date, time[datetime]',
      author: '.author, .writer',
      tags: '.tags a, .keywords a',
    };
  }

  protected async parseStaticPage(
    $: cheerio.Root,
    url: string
  ): Promise<CrawlResult> {
    const title = this.cleanText($(this.selectors.title).first().text());

    // 콘텐츠 추출
    let content = '';
    $(this.selectors.content).each((_, element) => {
      content += $(element).text() + '\n';
    });
    content = this.cleanText(content);

    // 메타데이터
    const metadata = this.extractMetadata($);

    // 날짜 추출
    const dateText = $(this.selectors.date).first().text();
    const dateAttr = $(this.selectors.date).first().attr('datetime');
    const publishDate = this.parseDate(dateAttr || dateText);

    // 저자 추출
    const author = this.cleanText($(this.selectors.author).first().text());

    // 태그 추출
    const tags: string[] = [];
    $(this.selectors.tags).each((_, element) => {
      const tag = this.cleanText($(element).text());
      if (tag) tags.push(tag);
    });

    // 링크 추출
    const links = this.extractLinks($, url);

    return {
      url,
      title,
      content,
      metadata: {
        ...metadata,
        publishDate,
        author: author || undefined,
        tags: tags.length > 0 ? tags : undefined,
      },
      links,
      success: true,
    };
  }

  protected async parseDynamicPage(
    $: cheerio.Root,
    page: Page,
    url: string
  ): Promise<CrawlResult> {
    // 동적 페이지도 정적 파싱과 동일하게 처리
    // 필요시 page 객체로 추가 조작 가능
    return this.parseStaticPage($, url);
  }

  /**
   * 셀렉터 업데이트
   */
  updateSelectors(selectors: Record<string, string>): void {
    this.selectors = { ...this.selectors, ...selectors };
  }
}

/**
 * PDF 문서 다운로더
 */
export class PDFDownloader {
  private axiosClient: AxiosInstance;

  constructor() {
    this.axiosClient = axios.create({
      timeout: 60000,
      responseType: 'arraybuffer',
    });
  }

  async download(url: string, savePath: string): Promise<boolean> {
    try {
      console.log(`[PDF] 다운로드 시작: ${url}`);
      const response = await this.axiosClient.get(url);

      const fs = await import('fs/promises');
      await fs.writeFile(savePath, response.data);

      console.log(`[PDF] 다운로드 완료: ${savePath}`);
      return true;
    } catch (error) {
      console.error(`[PDF] 다운로드 실패: ${url}`, error);
      return false;
    }
  }
}
