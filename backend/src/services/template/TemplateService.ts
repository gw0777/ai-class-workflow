import { TopicTemplate, TopicConfig, PromptTemplate } from '../../models/types';
import { ClaudeService } from '../claude/ClaudeService';

/**
 * 주제 템플릿 서비스
 * - 다양한 분야(체육, 교육, 의료, 환경 등)의 정책 분석 템플릿 관리
 * - 주제별 크롤링 설정, NLP 설정, 프롬프트 자동 생성
 */
export class TemplateService {
  private templates: Map<string, TopicTemplate>;

  constructor() {
    this.templates = new Map();
    this.initializeDefaultTemplates();
  }

  /**
   * 기본 템플릿 초기화
   */
  private initializeDefaultTemplates(): void {
    // 1. 장애인 체육 정책
    this.templates.set('disability_sports', {
      id: 'disability_sports',
      name: 'disability_sports',
      displayName: '장애인 체육 정책',
      description:
        '장애인 체육 진흥 정책, 법령, 조례 및 국제 기준 분석',
      category: '체육',
      config: {
        keywords: [
          '장애인',
          '체육',
          '생활체육',
          '전문체육',
          '반다비',
          '패럴림픽',
          '접근성',
          '유니버설디자인',
          '장애인체육회',
          '체육시설',
        ],
        sources: [
          {
            name: '문화체육관광부',
            type: 'government',
            url: 'https://www.mcst.go.kr',
          },
          {
            name: '대한장애인체육회',
            type: 'organization',
            url: 'https://www.koreanpc.kr',
          },
          {
            name: '국제패럴림픽위원회',
            type: 'international',
            url: 'https://www.paralympic.org',
          },
        ],
        documentTypes: ['정책문서', '법령', '조례', '가이드라인', '연구보고서'],
        nlpConfig: {
          language: 'ko',
          domainDict: 'disability_sports',
          entities: ['organization', 'law', 'program', 'facility', 'budget'],
        },
        crawlerConfig: {
          urls: [
            'https://www.mcst.go.kr',
            'https://www.koreanpc.kr',
            'https://www.law.go.kr',
          ],
          selectors: {
            title: 'h1, .title',
            content: '.content, article',
            date: '.date, time',
          },
        },
      },
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    // 2. 교육 정책
    this.templates.set('education', {
      id: 'education',
      name: 'education',
      displayName: '교육 정책',
      description: '초중고 및 고등교육 정책, 교육과정, 평가 제도 분석',
      category: '교육',
      config: {
        keywords: [
          '교육',
          '학습',
          '교육과정',
          '평가',
          '입시',
          '학생',
          '교사',
          '학교',
          '대학',
          '교육부',
        ],
        sources: [
          {
            name: '교육부',
            type: 'government',
            url: 'https://www.moe.go.kr',
          },
          {
            name: '한국교육과정평가원',
            type: 'organization',
            url: 'https://www.kice.re.kr',
          },
        ],
        documentTypes: ['정책문서', '법령', '교육과정', '연구보고서'],
        nlpConfig: {
          language: 'ko',
          domainDict: 'education',
          entities: ['organization', 'law', 'program', 'curriculum', 'budget'],
        },
        crawlerConfig: {
          urls: ['https://www.moe.go.kr', 'https://www.kice.re.kr'],
        },
      },
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    // 3. 보건의료 정책
    this.templates.set('healthcare', {
      id: 'healthcare',
      name: 'healthcare',
      displayName: '보건의료 정책',
      description: '의료 정책, 건강보험, 공중보건, 의료기관 관리',
      category: '보건',
      config: {
        keywords: [
          '의료',
          '건강',
          '병원',
          '건강보험',
          '진료',
          '공중보건',
          '질병',
          '예방',
          '치료',
          '보건복지부',
        ],
        sources: [
          {
            name: '보건복지부',
            type: 'government',
            url: 'https://www.mohw.go.kr',
          },
          {
            name: '건강보험심사평가원',
            type: 'organization',
            url: 'https://www.hira.or.kr',
          },
        ],
        documentTypes: ['정책문서', '법령', '가이드라인', '통계', '연구보고서'],
        nlpConfig: {
          language: 'ko',
          domainDict: 'healthcare',
          entities: ['organization', 'law', 'disease', 'treatment', 'budget'],
        },
        crawlerConfig: {
          urls: ['https://www.mohw.go.kr', 'https://www.hira.or.kr'],
        },
      },
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    // 4. 환경 정책
    this.templates.set('environment', {
      id: 'environment',
      name: 'environment',
      displayName: '환경 정책',
      description: '환경 보호, 기후 변화, 친환경 에너지, 탄소 중립',
      category: '환경',
      config: {
        keywords: [
          '환경',
          '기후',
          '탄소',
          '친환경',
          '재생에너지',
          '오염',
          '보전',
          '지속가능',
          '온실가스',
          '환경부',
        ],
        sources: [
          {
            name: '환경부',
            type: 'government',
            url: 'https://www.me.go.kr',
          },
          {
            name: '한국환경공단',
            type: 'organization',
            url: 'https://www.keco.or.kr',
          },
        ],
        documentTypes: ['정책문서', '법령', '통계', '보고서'],
        nlpConfig: {
          language: 'ko',
          domainDict: 'environment',
          entities: ['organization', 'law', 'pollutant', 'target', 'budget'],
        },
        crawlerConfig: {
          urls: ['https://www.me.go.kr', 'https://www.keco.or.kr'],
        },
      },
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    // 5. 과학기술 정책
    this.templates.set('science_technology', {
      id: 'science_technology',
      name: 'science_technology',
      displayName: '과학기술 정책',
      description: 'R&D, 기술 혁신, 디지털 전환, AI/ICT 정책',
      category: '과학기술',
      config: {
        keywords: [
          '과학',
          '기술',
          '연구개발',
          'R&D',
          '혁신',
          '디지털',
          'AI',
          'ICT',
          '스타트업',
          '과기정통부',
        ],
        sources: [
          {
            name: '과학기술정보통신부',
            type: 'government',
            url: 'https://www.msit.go.kr',
          },
          {
            name: '한국과학기술기획평가원',
            type: 'organization',
            url: 'https://www.kistep.re.kr',
          },
        ],
        documentTypes: ['정책문서', '법령', '기술보고서', '통계'],
        nlpConfig: {
          language: 'ko',
          domainDict: 'science_technology',
          entities: ['organization', 'law', 'technology', 'project', 'budget'],
        },
        crawlerConfig: {
          urls: ['https://www.msit.go.kr', 'https://www.kistep.re.kr'],
        },
      },
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
    });
  }

  /**
   * 템플릿 가져오기
   */
  getTemplate(name: string): TopicTemplate | undefined {
    return this.templates.get(name);
  }

  /**
   * 모든 템플릿 목록
   */
  getAllTemplates(): TopicTemplate[] {
    return Array.from(this.templates.values()).filter((t) => t.isActive);
  }

  /**
   * 카테고리별 템플릿 목록
   */
  getTemplatesByCategory(category: string): TopicTemplate[] {
    return Array.from(this.templates.values()).filter(
      (t) => t.category === category && t.isActive
    );
  }

  /**
   * 템플릿 추가
   */
  addTemplate(template: TopicTemplate): void {
    this.templates.set(template.name, template);
  }

  /**
   * 템플릿 업데이트
   */
  updateTemplate(name: string, updates: Partial<TopicTemplate>): boolean {
    const template = this.templates.get(name);
    if (!template) return false;

    const updated = { ...template, ...updates, updatedAt: new Date() };
    this.templates.set(name, updated);
    return true;
  }

  /**
   * 시스템 프롬프트 생성 (주제별)
   */
  generateSystemPrompt(topicName: string): string {
    const template = this.templates.get(topicName);
    if (!template) {
      throw new Error(`템플릿을 찾을 수 없습니다: ${topicName}`);
    }

    const keywords = template.config.keywords.join(', ');

    return `당신은 ${template.displayName} 분야의 정책 분석 전문가입니다.

**전문 분야:** ${template.description}

**핵심 키워드:** ${keywords}

**주요 문서 유형:**
${template.config.documentTypes.map((type) => `- ${type}`).join('\n')}

**정보 출처:**
${template.config.sources.map((s) => `- ${s.name} (${s.type})`).join('\n')}

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
- 전문 용어 사용 시 설명 제공
- 한국어로 응답`;
  }

  /**
   * 주제별 도메인 키워드 추출
   */
  getDomainKeywords(topicName: string): string[] {
    const template = this.templates.get(topicName);
    return template?.config.keywords || [];
  }

  /**
   * 새로운 주제 템플릿 생성 (AI 기반)
   */
  async createTemplateFromDescription(
    name: string,
    displayName: string,
    description: string,
    category: string
  ): Promise<TopicTemplate> {
    // Claude API를 사용하여 템플릿 설정 자동 생성
    const claudeService = new ClaudeService();

    const prompt = `다음 주제에 대한 정책 분석 시스템 설정을 생성해주세요:

**주제명:** ${displayName}
**설명:** ${description}
**카테고리:** ${category}

다음 정보를 JSON 형식으로 제공해주세요:
1. keywords: 핵심 키워드 10-15개 (배열)
2. sources: 주요 정보 출처 3-5개 (name, type, url)
3. documentTypes: 수집할 문서 유형 (배열)
4. entities: 추출할 엔티티 유형 (배열)

JSON만 출력하고 다른 설명은 제외해주세요.`;

    try {
      const response = await claudeService.simpleQuery(prompt, undefined, 'sonnet');
      const config = JSON.parse(response);

      const template: TopicTemplate = {
        id: name,
        name,
        displayName,
        description,
        category,
        config: {
          keywords: config.keywords || [],
          sources: config.sources || [],
          documentTypes: config.documentTypes || [],
          nlpConfig: {
            language: 'ko',
            domainDict: name,
            entities: config.entities || [],
          },
          crawlerConfig: {
            urls: config.sources?.map((s: any) => s.url).filter(Boolean) || [],
          },
        },
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      this.addTemplate(template);
      return template;
    } catch (error) {
      console.error('[Template] AI 템플릿 생성 실패:', error);

      // 기본 템플릿 반환
      return {
        id: name,
        name,
        displayName,
        description,
        category,
        config: {
          keywords: [],
          sources: [],
          documentTypes: ['정책문서', '법령', '보고서'],
          nlpConfig: {
            language: 'ko',
            entities: ['organization', 'law', 'budget'],
          },
          crawlerConfig: {
            urls: [],
          },
        },
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
    }
  }
}

/**
 * 프롬프트 최적화 도구
 * - 프롬프트 품질 평가
 * - 개선 제안
 * - A/B 테스트 지원
 */
export class PromptOptimizer {
  private claudeService: ClaudeService;

  constructor() {
    this.claudeService = new ClaudeService();
  }

  /**
   * 프롬프트 평가
   */
  async evaluatePrompt(prompt: string): Promise<{
    score: number;
    feedback: string;
    suggestions: string[];
  }> {
    const evaluationPrompt = `다음 프롬프트를 평가해주세요:

\`\`\`
${prompt}
\`\`\`

**평가 기준:**
1. 명확성 (Clear instructions)
2. 구체성 (Specific requirements)
3. 컨텍스트 제공 (Context)
4. 출력 형식 지정 (Output format)
5. 예시 제공 (Examples)

**출력 형식:**
{
  "score": 0-100,
  "feedback": "전반적인 평가",
  "suggestions": ["개선 제안 1", "개선 제안 2", ...]
}

JSON만 출력하세요.`;

    try {
      const response = await this.claudeService.simpleQuery(
        evaluationPrompt,
        undefined,
        'sonnet'
      );
      return JSON.parse(response);
    } catch (error) {
      console.error('[PromptOptimizer] 평가 실패:', error);
      return {
        score: 50,
        feedback: '평가를 완료할 수 없습니다.',
        suggestions: [],
      };
    }
  }

  /**
   * 프롬프트 개선
   */
  async improvePrompt(prompt: string): Promise<string> {
    const improvementPrompt = `다음 프롬프트를 개선해주세요:

\`\`\`
${prompt}
\`\`\`

**개선 방향:**
- 더 명확한 지시사항
- 구체적인 요구사항
- 출력 형식 명시
- 예시 추가 (필요시)
- 제약사항 명시

개선된 프롬프트만 출력하고 추가 설명은 제외하세요.`;

    try {
      return await this.claudeService.simpleQuery(
        improvementPrompt,
        undefined,
        'sonnet'
      );
    } catch (error) {
      console.error('[PromptOptimizer] 개선 실패:', error);
      return prompt;
    }
  }
}
