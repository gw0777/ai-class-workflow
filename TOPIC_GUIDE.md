# 주제 확장 가이드: 다른 분야에 시스템 적용하기

이 가이드는 장애인 체육 외 다른 분야(교육, 의료, 환경 등)에 범용 정책 분석 플랫폼을 적용하는 방법을 설명합니다.

## 방법 1: 사전 정의된 템플릿 사용

시스템에는 5개의 사전 정의된 주제 템플릿이 포함되어 있습니다:

1. **장애인 체육** (disability_sports)
2. **교육 정책** (education)
3. **보건의료** (healthcare)
4. **환경 정책** (environment)
5. **과학기술** (science_technology)

### 사용 방법

프론트엔드에서 주제를 선택하면 자동으로 해당 템플릿이 적용됩니다:

```typescript
// 예: 교육 정책 선택
<TemplateSelector
  selectedTopic="education"
  onSelectTopic={setSelectedTopic}
/>

// RAG 쿼리 시 자동으로 교육 관련 시스템 프롬프트 적용
const result = await ragQuery({
  query: "2024년 고교학점제 시행 계획은?",
  topicName: "education"
});
```

각 템플릿에는 다음이 포함됩니다:
- **키워드**: 해당 분야의 핵심 용어 10-15개
- **데이터 소스**: 주요 기관 및 웹사이트
- **문서 유형**: 수집할 문서 종류
- **NLP 설정**: 언어, 엔티티 추출 유형
- **크롤러 설정**: 크롤링 대상 URL

## 방법 2: AI 기반 자동 템플릿 생성

새로운 분야를 추가하려면 Claude API가 자동으로 템플릿을 생성합니다.

### API 호출

```bash
curl -X POST http://localhost:5000/api/templates/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urban_planning",
    "displayName": "도시계획 정책",
    "description": "도시개발, 주거정책, 교통계획, 재개발 분석",
    "category": "국토"
  }'
```

### 응답 예시

```json
{
  "success": true,
  "data": {
    "id": "urban_planning",
    "name": "urban_planning",
    "displayName": "도시계획 정책",
    "description": "도시개발, 주거정책, 교통계획, 재개발 분석",
    "category": "국토",
    "config": {
      "keywords": [
        "도시계획", "주거", "교통", "개발", "재개발",
        "주택", "도로", "공원", "인프라", "토지이용"
      ],
      "sources": [
        {
          "name": "국토교통부",
          "type": "government",
          "url": "https://www.molit.go.kr"
        },
        {
          "name": "한국토지주택공사",
          "type": "organization",
          "url": "https://www.lh.or.kr"
        }
      ],
      "documentTypes": ["정책문서", "법령", "계획서", "연구보고서"],
      "nlpConfig": {
        "language": "ko",
        "domainDict": "urban_planning",
        "entities": ["organization", "law", "project", "area", "budget"]
      },
      "crawlerConfig": {
        "urls": [
          "https://www.molit.go.kr",
          "https://www.lh.or.kr"
        ]
      }
    },
    "isActive": true
  }
}
```

Claude API가 자동으로:
- 관련 키워드 추출
- 주요 데이터 소스 식별
- 문서 유형 제안
- 엔티티 추출 설정

## 방법 3: 수동 템플릿 생성 (코드)

직접 코드를 수정하여 템플릿을 추가할 수 있습니다.

### 1. TemplateService에 템플릿 추가

`backend/src/services/template/TemplateService.ts` 파일을 편집:

```typescript
// 6. 사회복지 정책 추가
this.templates.set('social_welfare', {
  id: 'social_welfare',
  name: 'social_welfare',
  displayName: '사회복지 정책',
  description: '기초생활보장, 노인복지, 아동복지, 복지서비스',
  category: '복지',
  config: {
    keywords: [
      '사회복지',
      '기초생활보장',
      '노인복지',
      '아동복지',
      '장애인복지',
      '복지서비스',
      '생계급여',
      '의료급여',
      '주거급여',
      '교육급여',
    ],
    sources: [
      {
        name: '보건복지부',
        type: 'government',
        url: 'https://www.mohw.go.kr',
      },
      {
        name: '한국보건사회연구원',
        type: 'organization',
        url: 'https://www.kihasa.re.kr',
      },
    ],
    documentTypes: ['정책문서', '법령', '복지계획', '통계'],
    nlpConfig: {
      language: 'ko',
      domainDict: 'social_welfare',
      entities: ['organization', 'law', 'program', 'benefit', 'budget'],
    },
    crawlerConfig: {
      urls: [
        'https://www.mohw.go.kr',
        'https://www.kihasa.re.kr',
      ],
    },
  },
  isActive: true,
  createdAt: new Date(),
  updatedAt: new Date(),
});
```

### 2. 프론트엔드에 아이콘 추가

`frontend/src/components/TemplateSelector.tsx`:

```typescript
function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    체육: '⚽',
    교육: '📚',
    보건: '🏥',
    환경: '🌱',
    과학기술: '🔬',
    복지: '🤝',  // 새로 추가
    국토: '🏙️',  // 도시계획용
  };
  return icons[category] || '📄';
}
```

### 3. 서버 재시작

```bash
cd backend
npm run dev
```

## 방법 4: 커스텀 크롤러 어댑터 추가

특정 웹사이트에 맞춤형 크롤러를 추가하려면:

### 1. 새 크롤러 클래스 생성

`backend/src/services/crawler/CustomCrawlers.ts`:

```typescript
import { BaseCrawler, CrawlResult } from './BaseCrawler';
import * as cheerio from 'cheerio';
import { Page } from 'puppeteer';

/**
 * 국토교통부 전용 크롤러
 */
export class MOLITCrawler extends BaseCrawler {
  constructor() {
    super();
    // 국토부 사이트 특화 셀렉터
    this.updateSelectors({
      title: '.board_view .title',
      content: '.board_view .cont',
      date: '.board_view .date',
      author: '.board_view .writer',
    });
  }

  protected async parseStaticPage(
    $: cheerio.Root,
    url: string
  ): Promise<CrawlResult> {
    // 기본 파싱 수행
    const result = await super.parseStaticPage($, url);

    // 국토부 특화 처리
    // 예: 첨부파일 추출
    const attachments: string[] = [];
    $('.board_view .file a').each((_, element) => {
      const fileUrl = $(element).attr('href');
      if (fileUrl) {
        attachments.push(fileUrl);
      }
    });

    result.metadata.attachments = attachments;

    return result;
  }
}

/**
 * 교육부 전용 크롤러
 */
export class MOECrawler extends BaseCrawler {
  constructor() {
    super();
    this.updateSelectors({
      title: '.content_title',
      content: '.content_body',
      date: '.content_date',
    });
  }

  protected async waitForDynamicContent(page: Page): Promise<void> {
    // 교육부 사이트는 AJAX로 콘텐츠 로딩
    await page.waitForSelector('.content_body', { timeout: 10000 });
    await page.waitForTimeout(2000);
  }
}
```

### 2. 크롤러 사용

```typescript
import { MOLITCrawler, MOECrawler } from './services/crawler/CustomCrawlers';

// 국토부 크롤링
const molitCrawler = new MOLITCrawler();
const result = await molitCrawler.crawlStatic('https://www.molit.go.kr/...');

// 교육부 크롤링 (동적 페이지)
const moeCrawler = new MOECrawler();
const result = await moeCrawler.crawlDynamic('https://www.moe.go.kr/...');
```

## 주제별 프롬프트 최적화

각 주제마다 시스템 프롬프트가 자동 생성됩니다. 필요 시 수정 가능:

### 예시: 환경 정책

```typescript
const systemPrompt = `당신은 환경 정책 분야의 전문가입니다.

**전문 분야:**
- 기후변화 대응 정책
- 탄소중립 로드맵
- 재생에너지 정책
- 환경오염 규제

**핵심 키워드:**
환경, 기후, 탄소, 친환경, 재생에너지, 오염, 보전, 지속가능, 온실가스

**역할:**
- 환경 정책을 과학적 근거와 함께 분석합니다.
- 국제 환경 협약과 국내 정책을 연계하여 설명합니다.
- 온실가스 감축 목표, 환경 규제 기준 등 수치를 정확히 인용합니다.
- 환경과 경제의 균형을 고려한 객관적 분석을 제공합니다.

**답변 스타일:**
- 과학적 데이터 기반
- 국제 기준 참조
- 정량적 지표 제시
- 실현 가능성 평가
`;
```

## 데이터베이스 스키마 확장

새로운 주제에 특화된 필드가 필요한 경우:

### PostgreSQL 테이블 확장

```sql
-- 환경 정책 전용 필드 추가
ALTER TABLE policy_documents
ADD COLUMN greenhouse_gas_target DECIMAL(10, 2),
ADD COLUMN reduction_rate DECIMAL(5, 2),
ADD COLUMN compliance_deadline DATE;

-- 인덱스 추가
CREATE INDEX idx_policy_documents_ghg ON policy_documents(greenhouse_gas_target);
```

### MongoDB 스키마 (유연함)

```typescript
// MongoDB는 스키마리스이므로 자유롭게 필드 추가 가능
await documentsCollection.insertOne({
  title: '탄소중립 기본법 시행령',
  content: '...',
  metadata: {
    // 환경 정책 특화 필드
    targetYear: 2050,
    sectorGoals: {
      electricity: { reduction: 45.9, unit: '%' },
      transport: { reduction: 37.8, unit: '%' },
      industry: { reduction: 14.5, unit: '%' },
    },
    regulations: [
      '온실가스 배출권거래제',
      '신재생에너지 의무할당제',
    ],
  },
});
```

## 예시: 전체 워크플로우 (금융 정책 추가)

### 1. AI 템플릿 생성

```bash
curl -X POST http://localhost:5000/api/templates/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "financial_policy",
    "displayName": "금융 정책",
    "description": "통화정책, 금융규제, 금리정책, 금융안정",
    "category": "금융"
  }'
```

### 2. 데이터 수집

```typescript
// 금융위원회 크롤링
const crawler = new GenericPolicyCrawler({
  title: '.board-title',
  content: '.board-content',
  date: '.board-date',
});

const urls = [
  'https://www.fsc.go.kr/...',
  'https://www.bok.or.kr/...',
];

for (const url of urls) {
  const result = await crawler.crawlStatic(url);
  // DB 저장 및 임베딩
}
```

### 3. 문서 임베딩

```typescript
const vectorService = new VectorService();
const documentEmbeddingService = new DocumentEmbeddingService(vectorService);

// 문서를 청크로 분할하고 임베딩
await documentEmbeddingService.embedDocument(documentId, chunks);
```

### 4. RAG 쿼리

```typescript
const result = await ragQuery({
  query: '2024년 기준금리 인상 배경은?',
  topicName: 'financial_policy',
  model: 'sonnet',
});
```

## 주제별 키워드 및 프롬프트 가이드

| 주제 | 핵심 키워드 | 프롬프트 예시 |
|------|-------------|---------------|
| **장애인 체육** | 생활체육, 전문체육, 반다비, 접근성 | "장애인 체육시설 접근성 기준은?" |
| **교육 정책** | 교육과정, 입시, 평가, 학습 | "2024년 고교학점제 주요 내용은?" |
| **보건의료** | 건강보험, 진료, 공중보건, 의료기관 | "건강보험 보장성 강화 정책은?" |
| **환경 정책** | 기후, 탄소, 재생에너지, 온실가스 | "2050 탄소중립 목표 달성 방안은?" |
| **과학기술** | R&D, 혁신, AI, ICT, 디지털 | "디지털 전환 정책 주요 내용은?" |
| **도시계획** | 주거, 교통, 개발, 재개발, 토지 | "수도권 주택공급 계획은?" |
| **사회복지** | 기초생활보장, 노인복지, 급여 | "기초생활수급자 선정 기준은?" |
| **금융 정책** | 통화정책, 금리, 금융규제, 안정 | "기준금리 인하 배경과 전망은?" |

## 모범 사례

### 1. 키워드 선정
- 10-15개의 핵심 키워드
- 일반 용어 + 전문 용어 혼합
- 약어 포함 (예: R&D, ICT, AI)

### 2. 데이터 소스
- 정부 부처 (1순위)
- 공공기관/연구원 (2순위)
- 국제 기구 (3순위)
- 학술지/협회 (4순위)

### 3. 문서 유형
- 필수: 정책문서, 법령
- 선택: 통계, 연구보고서, 백서, 가이드라인

### 4. NLP 엔티티
- 공통: organization, law, budget
- 주제별 추가:
  - 체육: facility, program, athlete
  - 교육: curriculum, school, student
  - 환경: pollutant, target, regulation

## 문제 해결

### Q: 새 주제의 검색 정확도가 낮아요
A:
1. 도메인 키워드를 더 추가하세요
2. `minScore`를 낮춰보세요 (0.7 → 0.6)
3. 더 많은 문서를 수집하세요 (최소 100개 권장)

### Q: 특정 웹사이트 크롤링이 안 돼요
A:
1. 동적 페이지인지 확인 (`crawlDynamic` 사용)
2. 셀렉터가 정확한지 확인
3. 커스텀 크롤러 어댑터 작성 고려

### Q: AI 답변이 주제와 맞지 않아요
A:
1. 시스템 프롬프트를 더 구체적으로 작성
2. 검색된 문서의 관련성 확인 (`score` 값)
3. 주제 템플릿의 키워드 재검토

## 추가 리소스

- [Claude API 문서](https://docs.anthropic.com/)
- [RAG 구현 가이드](https://www.anthropic.com/index/building-effective-agents)
- [Vector Database 최적화](https://qdrant.tech/documentation/tutorials/optimize/)

---

**Happy Building! 🚀**
