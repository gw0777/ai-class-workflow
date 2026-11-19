# PDF/PPTX 변환 기능

이 모듈은 기존 교육 자료(PDF, PPTX)를 시스템의 교재 형식으로 자동 변환하는 기능을 제공합니다.

## 기능 개요

### 지원 형식

- **PDF**: PDF 파일에서 텍스트를 추출하고 챕터/섹션으로 구조화
- **PPTX**: PowerPoint 프레젠테이션을 슬라이드 기반으로 변환
- **DOCX**: Word 문서 (향후 지원 예정)

## 변환 프로세스

### 1. 파일 업로드

```bash
POST /api/converter/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: [PDF/PPTX 파일]
```

응답:
```json
{
  "success": true,
  "message": "파일이 성공적으로 업로드되었습니다.",
  "data": {
    "id": "source-material-id",
    "filename": "original-file.pdf",
    "fileType": "application/pdf",
    "fileSize": 1024000,
    "uploadedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### 2. PDF 변환

```bash
POST /api/converter/convert/pdf/{sourceId}
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "교재 제목",
  "subtitle": "부제목",
  "author": "저자명",
  "subject": "과목명",
  "targetAudience": "대상 독자",
  "difficulty": "intermediate",
  "keywords": ["키워드1", "키워드2"]
}
```

### 3. PPTX 변환

```bash
POST /api/converter/convert/pptx/{sourceId}
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "교재 제목",
  "subtitle": "부제목",
  "author": "저자명",
  "subject": "과목명",
  "targetAudience": "대상 독자",
  "difficulty": "intermediate",
  "keywords": ["키워드1", "키워드2"]
}
```

## PDF 변환 로직

### 텍스트 추출

`pdf-parse` 라이브러리를 사용하여 PDF에서 텍스트를 추출합니다.

### 구조 인식

다음 패턴을 인식하여 챕터와 섹션으로 분리합니다:

**챕터 인식 패턴:**
- `제 N 장`
- `Chapter N`
- `챕터 N`
- `제 N 과`

**섹션 인식 패턴:**
- `N.N` (예: 1.1, 2.3)
- `N-N` (예: 1-1, 2-3)
- `제 N 절`

**학습 목표 인식:**
- "학습목표" 또는 "학습 목표" 키워드 후의 리스트 항목
- 불릿 포인트 (`•`, `-`, `*`, `1.`, `2.` 등)

### 예시

```
제1장 직접교수 모형

학습목표:
• 직접교수 모형의 개념을 설명할 수 있다
• 직접교수 모형의 단계를 이해한다

1.1 직접교수 모형이란?

직접교수 모형은 교사 중심의 체계적인 교수 방법입니다...
```

위 내용은 다음과 같이 변환됩니다:

- **챕터**: "제1장 직접교수 모형"
- **학습 목표**:
  - "직접교수 모형의 개념을 설명할 수 있다"
  - "직접교수 모형의 단계를 이해한다"
- **섹션**: "1.1 직접교수 모형이란?"
- **내용**: "직접교수 모형은 교사 중심의..."

## PPTX 변환 로직

### 슬라이드 추출

각 슬라이드를 개별 단위로 추출합니다.

### 챕터 인식

슬라이드 제목이 챕터 패턴과 일치하면 새로운 챕터로 인식합니다.

### 슬라이드 매핑

- 챕터 슬라이드: 새로운 챕터 시작
- 일반 슬라이드: 현재 챕터의 섹션으로 추가

## 사용 예시

### 기존 PDF 교재 변환

```javascript
// 1. 파일 업로드
const formData = new FormData();
formData.append('file', pdfFile);

const uploadResponse = await fetch('/api/converter/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const { data: sourceMaterial } = await uploadResponse.json();

// 2. 변환 실행
const convertResponse = await fetch(`/api/converter/convert/pdf/${sourceMaterial.id}`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: '스포츠 교육학 기초',
    author: '김체육',
    subject: '체육교육',
    targetAudience: '예비 체육교사',
    difficulty: 'intermediate',
    keywords: ['체육', '교육학', '스포츠']
  })
});

const { data: textbook } = await convertResponse.json();
console.log('변환 완료:', textbook);
```

## 변환 결과 구조

```json
{
  "id": "textbook-id",
  "title": "스포츠 교육학 기초",
  "author": "김체육",
  "status": "DRAFT",
  "chapters": [
    {
      "number": 1,
      "title": "제1장 체육 교육학의 이해",
      "content": "...",
      "learningObjectives": [
        "체육 교육학의 개념을 설명할 수 있다",
        "체육 교육의 목표를 이해한다"
      ],
      "sections": [
        {
          "title": "1.1 체육 교육학의 정의",
          "content": "...",
          "order": 0
        }
      ]
    }
  ],
  "metadata": {
    "subject": "체육교육",
    "targetAudience": "예비 체육교사",
    "difficulty": "intermediate",
    "keywords": ["체육", "교육학", "스포츠"],
    "source": {
      "type": "pdf",
      "pages": 150
    }
  }
}
```

## 제한 사항

### 현재 버전

- PDF 텍스트 추출은 텍스트 기반 PDF만 지원 (스캔 PDF는 OCR 필요)
- PPTX 변환은 기본 구현 (추가 라이브러리 필요)
- 이미지, 표, 그래프는 현재 버전에서 지원하지 않음
- 복잡한 레이아웃은 수동 편집이 필요할 수 있음

### 향후 개선 사항

- OCR 지원으로 스캔 PDF 처리
- 이미지 및 그래프 추출
- 표 구조 인식 및 변환
- AI 기반 자동 요약 및 학습 목표 생성
- 더 정교한 구조 인식 알고리즘

## 수동 편집

변환된 교재는 `DRAFT` 상태로 생성되므로, 편집자가 다음 작업을 수행할 수 있습니다:

1. 챕터 제목 및 순서 조정
2. 학습 목표 수정 및 보완
3. 내용 재구성 및 편집
4. 평가 문항 추가
5. 이미지 및 보충 자료 추가

## 소스 자료 관리

### 소스 자료 조회

```bash
GET /api/converter/materials?page=1&limit=10
Authorization: Bearer {token}
```

### 소스 자료 삭제

```bash
DELETE /api/converter/materials/{id}
Authorization: Bearer {token}
```

## 보안

- 파일 업로드는 인증된 편집자 이상만 가능
- 파일 크기 제한: 50MB (환경 변수로 설정 가능)
- 허용된 파일 형식만 업로드 가능
- 업로드된 파일은 서버의 `uploads/` 디렉토리에 저장

## 환경 설정

`.env` 파일에서 다음 설정을 조정할 수 있습니다:

```env
# 최대 파일 크기 (바이트)
MAX_FILE_SIZE=52428800

# 업로드 디렉토리
UPLOAD_DIR=uploads
```
