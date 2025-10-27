import Anthropic from '@anthropic-ai/sdk';
import { RAGQuery, RAGResult, RetrievedDocument } from '../../models/types';

/**
 * Claude API 서비스
 * - Prompt Caching으로 비용 90% 절감
 * - Haiku/Sonnet 모델 선택 전략
 * - RAG 파이프라인 통합
 */
export class ClaudeService {
  private client: Anthropic;
  private modelHaiku: string;
  private modelSonnet: string;

  constructor() {
    this.client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });

    this.modelHaiku =
      process.env.CLAUDE_MODEL_HAIKU || 'claude-3-haiku-20240307';
    this.modelSonnet =
      process.env.CLAUDE_MODEL_SONNET || 'claude-3-5-sonnet-20241022';
  }

  /**
   * RAG 쿼리 실행
   * @param query 사용자 질문
   * @param retrievedDocs Vector DB에서 검색된 문서
   * @param systemPrompt 시스템 프롬프트 (캐싱 가능)
   * @param useCache Prompt Caching 사용 여부
   * @param model 사용할 모델 ('haiku' | 'sonnet')
   */
  async ragQuery(
    query: string,
    retrievedDocs: RetrievedDocument[],
    systemPrompt: string,
    useCache: boolean = true,
    model: 'haiku' | 'sonnet' = 'sonnet'
  ): Promise<RAGResult> {
    const startTime = Date.now();

    try {
      // 컨텍스트 구성
      const context = this.buildContext(retrievedDocs);

      // 모델 선택
      const selectedModel = model === 'haiku' ? this.modelHaiku : this.modelSonnet;

      // 메시지 구성 (Prompt Caching 적용)
      const messages: Anthropic.MessageParam[] = [
        {
          role: 'user',
          content: this.buildUserPrompt(query, context),
        },
      ];

      // 시스템 프롬프트 설정 (캐싱)
      const systemMessages: Anthropic.Messages.MessageCreateParams['system'] = useCache
        ? [
            {
              type: 'text',
              text: systemPrompt,
              cache_control: { type: 'ephemeral' },
            },
          ]
        : systemPrompt;

      console.log(`[Claude] RAG 쿼리 시작 - Model: ${selectedModel}, Cache: ${useCache}`);

      // Claude API 호출
      const response = await this.client.messages.create({
        model: selectedModel,
        max_tokens: parseInt(process.env.CLAUDE_MAX_TOKENS || '4096'),
        temperature: parseFloat(process.env.CLAUDE_TEMPERATURE || '0.7'),
        system: systemMessages,
        messages,
      });

      const responseTime = Date.now() - startTime;

      // 사용량 정보
      const usage = response.usage;
      const inputTokens = usage.input_tokens || 0;
      const outputTokens = usage.output_tokens || 0;

      // cache_read_input_tokens는 Anthropic SDK 타입에 포함되어 있을 수 있음
      const cachedTokens = (usage as any).cache_read_input_tokens || 0;

      // 비용 계산
      const cost = this.calculateCost(
        selectedModel,
        inputTokens,
        outputTokens,
        cachedTokens
      );

      console.log(
        `[Claude] 완료 - 응답시간: ${responseTime}ms, 입력: ${inputTokens}, 출력: ${outputTokens}, 캐시: ${cachedTokens}, 비용: $${cost.toFixed(6)}`
      );

      // 응답 텍스트 추출
      const answerContent = response.content.find((c) => c.type === 'text');
      const answer = answerContent && 'text' in answerContent ? answerContent.text : '';

      return {
        answer,
        sources: retrievedDocs,
        confidence: this.estimateConfidence(retrievedDocs),
        metadata: {
          model: selectedModel,
          inputTokens,
          outputTokens,
          cachedTokens,
          responseTimeMs: responseTime,
          costUsd: cost,
        },
      };
    } catch (error) {
      console.error('[Claude] RAG 쿼리 실패:', error);
      throw error;
    }
  }

  /**
   * 간단한 쿼리 (RAG 없이)
   */
  async simpleQuery(
    query: string,
    systemPrompt?: string,
    model: 'haiku' | 'sonnet' = 'haiku'
  ): Promise<string> {
    const selectedModel = model === 'haiku' ? this.modelHaiku : this.modelSonnet;

    const response = await this.client.messages.create({
      model: selectedModel,
      max_tokens: 2048,
      temperature: 0.7,
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: query,
        },
      ],
    });

    const answerContent = response.content.find((c) => c.type === 'text');
    return answerContent && 'text' in answerContent ? answerContent.text : '';
  }

  /**
   * 컨텍스트 구성
   */
  private buildContext(docs: RetrievedDocument[]): string {
    if (docs.length === 0) {
      return '(검색된 관련 문서가 없습니다.)';
    }

    const contextParts = docs.map((doc, index) => {
      const metadata = [
        `**출처 ${index + 1}**`,
        `- 제목: ${doc.title}`,
        doc.metadata.publisher && `- 발행기관: ${doc.metadata.publisher}`,
        doc.metadata.publishDate &&
          `- 발행일: ${new Date(doc.metadata.publishDate).toLocaleDateString('ko-KR')}`,
        doc.metadata.documentType && `- 문서유형: ${doc.metadata.documentType}`,
        doc.metadata.url && `- URL: ${doc.metadata.url}`,
        `- 유사도: ${(doc.score * 100).toFixed(1)}%`,
        '',
        `**내용:**`,
        doc.content,
        '',
        '---',
      ]
        .filter(Boolean)
        .join('\n');

      return metadata;
    });

    return contextParts.join('\n\n');
  }

  /**
   * 사용자 프롬프트 구성
   */
  private buildUserPrompt(query: string, context: string): string {
    return `다음은 정책 문서 데이터베이스에서 검색된 관련 문서들입니다:

${context}

위 문서들을 참고하여 다음 질문에 답변해주세요:

**질문:** ${query}

**답변 가이드라인:**
1. 검색된 문서의 정보를 기반으로 정확하게 답변하세요.
2. 출처를 명시하여 답변의 신뢰성을 높이세요.
3. 문서에 없는 내용은 추측하지 말고 "문서에서 확인할 수 없습니다"라고 밝히세요.
4. 수치, 날짜, 고유명사는 정확히 인용하세요.
5. 가능하면 여러 출처의 정보를 종합하여 답변하세요.

답변:`;
  }

  /**
   * 신뢰도 추정 (검색 점수 기반)
   */
  private estimateConfidence(docs: RetrievedDocument[]): number {
    if (docs.length === 0) return 0;

    // 상위 3개 문서의 평균 점수
    const topDocs = docs.slice(0, 3);
    const avgScore =
      topDocs.reduce((sum, doc) => sum + doc.score, 0) / topDocs.length;

    return Math.min(avgScore, 1.0);
  }

  /**
   * 비용 계산 (2024년 기준 가격)
   * - Haiku: $0.00025 / 1K input, $0.00125 / 1K output
   * - Sonnet: $0.003 / 1K input, $0.015 / 1K output
   * - Cache Read: $0.00003 / 1K (Haiku), $0.0003 / 1K (Sonnet)
   */
  private calculateCost(
    model: string,
    inputTokens: number,
    outputTokens: number,
    cachedTokens: number
  ): number {
    const isHaiku = model.includes('haiku');

    const inputPrice = isHaiku ? 0.00025 : 0.003;
    const outputPrice = isHaiku ? 0.00125 : 0.015;
    const cachePrice = isHaiku ? 0.00003 : 0.0003;

    const inputCost = (inputTokens / 1000) * inputPrice;
    const outputCost = (outputTokens / 1000) * outputPrice;
    const cacheCost = (cachedTokens / 1000) * cachePrice;

    return inputCost + outputCost - cacheCost;
  }

  /**
   * 정책 비교 분석
   */
  async comparePolicies(
    policies: { title: string; content: string }[],
    criteria: string[]
  ): Promise<string> {
    const policiesText = policies
      .map(
        (p, i) =>
          `**정책 ${i + 1}: ${p.title}**\n${p.content}\n\n---\n`
      )
      .join('\n');

    const criteriaText = criteria
      .map((c, i) => `${i + 1}. ${c}`)
      .join('\n');

    const prompt = `다음 정책들을 비교 분석해주세요:

${policiesText}

**비교 기준:**
${criteriaText}

각 정책의 특징, 차이점, 장단점을 표로 정리하고, 종합적인 분석을 제공해주세요.`;

    return this.simpleQuery(prompt, undefined, 'sonnet');
  }

  /**
   * 트렌드 분석
   */
  async analyzeTrend(
    documents: { date: Date; title: string; summary: string }[]
  ): Promise<string> {
    const sortedDocs = documents.sort(
      (a, b) => a.date.getTime() - b.date.getTime()
    );

    const timeline = sortedDocs
      .map(
        (doc) =>
          `- ${doc.date.toLocaleDateString('ko-KR')}: ${doc.title}\n  ${doc.summary}`
      )
      .join('\n\n');

    const prompt = `다음은 시계열 순으로 정리된 정책 문서들입니다:

${timeline}

이 정책들의 변화 추이를 분석하여 다음을 설명해주세요:
1. 주요 정책 변화의 흐름
2. 새롭게 등장한 주제나 키워드
3. 강화되거나 약화된 정책 방향
4. 향후 예상되는 정책 방향`;

    return this.simpleQuery(prompt, undefined, 'sonnet');
  }

  /**
   * 시스템 프롬프트 생성 (주제별)
   */
  static generateSystemPrompt(
    topicName: string,
    domainKeywords: string[],
    expertise: string[]
  ): string {
    return `당신은 ${topicName} 분야의 정책 분석 전문가입니다.

**전문 분야:**
${expertise.map((e) => `- ${e}`).join('\n')}

**핵심 키워드:**
${domainKeywords.join(', ')}

**역할:**
- 정책 문서를 정확하게 분석하고 해석합니다.
- 복잡한 정책 내용을 명확하고 이해하기 쉽게 설명합니다.
- 여러 정책 문서를 비교하고 종합적인 인사이트를 제공합니다.
- 통계 수치, 날짜, 고유명사 등을 정확히 인용합니다.
- 객관적이고 중립적인 관점을 유지합니다.

**답변 스타일:**
- 명확하고 구조화된 답변
- 출처 명시
- 근거 기반 분석
- 전문 용어 사용 시 설명 제공`;
  }
}

/**
 * Prompt Template Manager
 */
export class PromptTemplateManager {
  private templates: Map<string, string>;

  constructor() {
    this.templates = new Map();
    this.initializeDefaultTemplates();
  }

  /**
   * 기본 템플릿 초기화
   */
  private initializeDefaultTemplates(): void {
    // 정책 요약 템플릿
    this.templates.set(
      'policy_summary',
      `다음 정책 문서를 요약해주세요:

{content}

**요약 항목:**
1. 정책 목표
2. 주요 내용
3. 대상 및 범위
4. 예산 및 기간
5. 기대 효과`
    );

    // 법령 분석 템플릿
    this.templates.set(
      'law_analysis',
      `다음 법령을 분석해주세요:

{content}

**분석 항목:**
1. 제정 목적
2. 주요 조항
3. 적용 대상
4. 규제 내용
5. 벌칙 사항`
    );

    // 예산 분석 템플릿
    this.templates.set(
      'budget_analysis',
      `다음 예산 정책을 분석해주세요:

{content}

**분석 항목:**
1. 총 예산 규모
2. 주요 지출 항목
3. 전년 대비 변화
4. 예산 배분 우선순위
5. 예상되는 효과`
    );
  }

  /**
   * 템플릿 가져오기
   */
  getTemplate(name: string, variables: Record<string, string>): string {
    const template = this.templates.get(name);
    if (!template) {
      throw new Error(`템플릿 '${name}'을 찾을 수 없습니다.`);
    }

    return this.interpolate(template, variables);
  }

  /**
   * 템플릿 추가
   */
  addTemplate(name: string, template: string): void {
    this.templates.set(name, template);
  }

  /**
   * 변수 치환
   */
  private interpolate(
    template: string,
    variables: Record<string, string>
  ): string {
    let result = template;
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`{${key}}`, 'g'), value);
    });
    return result;
  }

  /**
   * 모든 템플릿 목록
   */
  listTemplates(): string[] {
    return Array.from(this.templates.keys());
  }
}
