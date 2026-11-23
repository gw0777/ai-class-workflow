import natural from 'natural';
import { removeStopwords } from 'stopword';

/**
 * NLP 처리 레이어
 * - 텍스트 정규화
 * - 토큰화
 * - 키워드 추출
 * - 청크 분할
 */
export class TextProcessor {
  private tokenizer: natural.WordTokenizer;
  private tfidf: natural.TfIdf;
  private domainKeywords: Set<string>;

  constructor(domainKeywords: string[] = []) {
    this.tokenizer = new natural.WordTokenizer();
    this.tfidf = new natural.TfIdf();
    this.domainKeywords = new Set(domainKeywords);
  }

  /**
   * 텍스트 정규화
   */
  normalize(text: string): string {
    return text
      .replace(/[\r\n]+/g, '\n') // 줄바꿈 정규화
      .replace(/\s+/g, ' ') // 공백 정규화
      .replace(/[^\w\sㄱ-ㅎ가-힣a-zA-Z0-9.,!?;:()\-]/g, '') // 특수문자 제거
      .trim();
  }

  /**
   * 토큰화 (한국어 + 영어)
   */
  tokenize(text: string): string[] {
    // 영문 토큰화
    const tokens = this.tokenizer.tokenize(text.toLowerCase()) || [];

    // 한글 토큰화 (간단한 공백 기반)
    const koreanTokens = text
      .split(/\s+/)
      .filter((token) => /[가-힣]/.test(token));

    return [...tokens, ...koreanTokens];
  }

  /**
   * 불용어 제거
   */
  removeStopwords(tokens: string[]): string[] {
    // 영어 불용어 제거
    const filteredTokens = removeStopwords(tokens);

    // 한국어 불용어 (확장 가능)
    const koreanStopwords = new Set([
      '이',
      '그',
      '저',
      '것',
      '수',
      '등',
      '들',
      '및',
      '또한',
      '위해',
      '통해',
      '대한',
      '있다',
      '없다',
      '하다',
      '되다',
      '이다',
      '아니다',
    ]);

    return filteredTokens.filter((token) => !koreanStopwords.has(token));
  }

  /**
   * TF-IDF 기반 키워드 추출
   */
  extractKeywords(
    text: string,
    topN: number = 10,
    minLength: number = 2
  ): string[] {
    const normalized = this.normalize(text);
    const tokens = this.tokenize(normalized);
    const filtered = this.removeStopwords(tokens);

    // TF-IDF 계산
    this.tfidf.addDocument(filtered);

    const keywords: { term: string; score: number }[] = [];
    const docIndex = this.tfidf.documents.length - 1;

    this.tfidf.listTerms(docIndex).forEach((item) => {
      if (item.term.length >= minLength) {
        // 도메인 키워드 부스팅
        const boost = this.domainKeywords.has(item.term) ? 1.5 : 1.0;
        keywords.push({
          term: item.term,
          score: item.tfidf * boost,
        });
      }
    });

    // 점수순 정렬 및 상위 N개 반환
    return keywords
      .sort((a, b) => b.score - a.score)
      .slice(0, topN)
      .map((k) => k.term);
  }

  /**
   * 문서 청크 분할 (RAG용)
   * @param text 원본 텍스트
   * @param chunkSize 청크 크기 (토큰 수)
   * @param overlap 오버랩 크기 (토큰 수)
   */
  chunkText(
    text: string,
    chunkSize: number = 512,
    overlap: number = 50
  ): string[] {
    const normalized = this.normalize(text);
    const sentences = this.splitIntoSentences(normalized);

    const chunks: string[] = [];
    let currentChunk: string[] = [];
    let currentTokenCount = 0;

    for (const sentence of sentences) {
      const sentenceTokens = this.tokenize(sentence);
      const tokenCount = sentenceTokens.length;

      if (currentTokenCount + tokenCount > chunkSize && currentChunk.length > 0) {
        // 현재 청크 저장
        chunks.push(currentChunk.join(' '));

        // 오버랩 처리: 마지막 N개 문장 유지
        const overlapTokens = Math.floor(overlap);
        let overlapCount = 0;
        const overlapChunk: string[] = [];

        for (let i = currentChunk.length - 1; i >= 0; i--) {
          const sent = currentChunk[i];
          const tokens = this.tokenize(sent);
          if (overlapCount + tokens.length <= overlapTokens) {
            overlapChunk.unshift(sent);
            overlapCount += tokens.length;
          } else {
            break;
          }
        }

        currentChunk = overlapChunk;
        currentTokenCount = overlapCount;
      }

      currentChunk.push(sentence);
      currentTokenCount += tokenCount;
    }

    // 마지막 청크 추가
    if (currentChunk.length > 0) {
      chunks.push(currentChunk.join(' '));
    }

    return chunks;
  }

  /**
   * 문장 분할
   */
  private splitIntoSentences(text: string): string[] {
    // 간단한 정규식 기반 문장 분할
    // 개선: KoNLPy, kss 등 라이브러리 사용 가능
    const sentences = text
      .split(/[.!?。]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    return sentences;
  }

  /**
   * 텍스트 요약 (추출적 요약)
   */
  summarize(text: string, sentenceCount: number = 3): string {
    const sentences = this.splitIntoSentences(text);

    if (sentences.length <= sentenceCount) {
      return text;
    }

    // TF-IDF 기반 문장 점수 계산
    const sentenceScores: { sentence: string; score: number }[] = [];

    sentences.forEach((sentence) => {
      const tokens = this.tokenize(sentence);
      const filtered = this.removeStopwords(tokens);

      this.tfidf.addDocument(filtered);
      const docIndex = this.tfidf.documents.length - 1;

      let score = 0;
      this.tfidf.listTerms(docIndex).forEach((item) => {
        score += item.tfidf;
      });

      sentenceScores.push({ sentence, score });
    });

    // 상위 N개 문장 선택 (원본 순서 유지)
    const topSentences = sentenceScores
      .sort((a, b) => b.score - a.score)
      .slice(0, sentenceCount)
      .map((s) => s.sentence);

    // 원본 순서대로 정렬
    const orderedSentences = sentences.filter((s) =>
      topSentences.includes(s)
    );

    return orderedSentences.join('. ') + '.';
  }

  /**
   * N-gram 추출
   */
  extractNGrams(text: string, n: number = 2): string[] {
    const tokens = this.tokenize(this.normalize(text));
    const filtered = this.removeStopwords(tokens);

    const ngrams: string[] = [];
    for (let i = 0; i <= filtered.length - n; i++) {
      const ngram = filtered.slice(i, i + n).join(' ');
      ngrams.push(ngram);
    }

    return ngrams;
  }

  /**
   * 도메인 키워드 추가
   */
  addDomainKeywords(keywords: string[]): void {
    keywords.forEach((keyword) => this.domainKeywords.add(keyword));
  }
}

/**
 * 간단한 Named Entity Recognition
 * (실제 운영 환경에서는 KoNLPy, spaCy 등 전문 라이브러리 사용 권장)
 */
export class SimpleNER {
  private patterns: Map<string, RegExp[]>;

  constructor() {
    this.patterns = new Map([
      // 날짜
      [
        'date',
        [
          /\d{4}년\s*\d{1,2}월\s*\d{1,2}일/g,
          /\d{4}-\d{2}-\d{2}/g,
          /\d{4}\.\d{2}\.\d{2}/g,
        ],
      ],
      // 금액
      [
        'budget',
        [
          /\d+(?:,\d{3})*\s*(?:원|달러|엔|유로)/g,
          /\$\s*\d+(?:,\d{3})*/g,
        ],
      ],
      // 법령
      ['law', [/[가-힣]+법(?:\s*제\d+조)?/g, /[가-힣]+조례/g]],
      // 기관명 (간단한 패턴)
      ['organization', [/[가-힣]+(?:부|청|원|회|단체|협회|재단)/g]],
    ]);
  }

  /**
   * 엔티티 추출
   */
  extractEntities(text: string): Map<string, string[]> {
    const entities = new Map<string, string[]>();

    this.patterns.forEach((patterns, entityType) => {
      const found: string[] = [];

      patterns.forEach((pattern) => {
        const matches = text.match(pattern);
        if (matches) {
          found.push(...matches);
        }
      });

      if (found.length > 0) {
        entities.set(entityType, [...new Set(found)]);
      }
    });

    return entities;
  }

  /**
   * 커스텀 패턴 추가
   */
  addPattern(entityType: string, pattern: RegExp): void {
    if (!this.patterns.has(entityType)) {
      this.patterns.set(entityType, []);
    }
    this.patterns.get(entityType)!.push(pattern);
  }
}

/**
 * 텍스트 유사도 계산
 */
export class TextSimilarity {
  /**
   * Jaccard 유사도
   */
  static jaccard(text1: string, text2: string): number {
    const tokens1 = new Set(text1.toLowerCase().split(/\s+/));
    const tokens2 = new Set(text2.toLowerCase().split(/\s+/));

    const intersection = new Set(
      [...tokens1].filter((token) => tokens2.has(token))
    );
    const union = new Set([...tokens1, ...tokens2]);

    return union.size === 0 ? 0 : intersection.size / union.size;
  }

  /**
   * Cosine 유사도 (TF-IDF 벡터 기반)
   */
  static cosine(text1: string, text2: string): number {
    const tfidf = new natural.TfIdf();
    tfidf.addDocument(text1);
    tfidf.addDocument(text2);

    const terms1 = new Map<string, number>();
    const terms2 = new Map<string, number>();

    tfidf.listTerms(0).forEach((item) => {
      terms1.set(item.term, item.tfidf);
    });

    tfidf.listTerms(1).forEach((item) => {
      terms2.set(item.term, item.tfidf);
    });

    // 코사인 유사도 계산
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    const allTerms = new Set([...terms1.keys(), ...terms2.keys()]);

    allTerms.forEach((term) => {
      const v1 = terms1.get(term) || 0;
      const v2 = terms2.get(term) || 0;

      dotProduct += v1 * v2;
      norm1 += v1 * v1;
      norm2 += v2 * v2;
    });

    const denominator = Math.sqrt(norm1) * Math.sqrt(norm2);
    return denominator === 0 ? 0 : dotProduct / denominator;
  }
}
