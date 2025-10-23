import pdf from 'pdf-parse';
import fs from 'fs/promises';

/**
 * PDF 파일을 텍스트로 변환
 */
export async function extractTextFromPDF(filePath) {
  try {
    const dataBuffer = await fs.readFile(filePath);
    const data = await pdf(dataBuffer);

    return {
      text: data.text,
      numPages: data.numpages,
      info: data.info,
      metadata: data.metadata,
    };
  } catch (error) {
    console.error('PDF 텍스트 추출 오류:', error);
    throw new Error('PDF 파일을 읽을 수 없습니다.');
  }
}

/**
 * PDF 내용을 구조화된 챕터로 변환
 * 제목 패턴을 인식하여 챕터와 섹션으로 분리
 */
export function structurePDFContent(text) {
  const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);

  const chapters = [];
  let currentChapter = null;
  let currentSection = null;
  let contentBuffer = [];

  // 제목 패턴 인식 (예: "1장", "Chapter 1", "제1장" 등)
  const chapterPattern = /^(?:제?\s*\d+\s*장|Chapter\s+\d+|챕터\s+\d+|제\s*\d+\s*과)/i;
  const sectionPattern = /^(?:\d+\.\d+|\d+-\d+|제\s*\d+\s*절)/i;

  for (const line of lines) {
    // 챕터 제목 감지
    if (chapterPattern.test(line)) {
      // 이전 섹션/챕터 저장
      if (currentSection && contentBuffer.length > 0) {
        currentSection.content = contentBuffer.join('\n\n');
        contentBuffer = [];
      }
      if (currentChapter && currentSection) {
        currentChapter.sections.push(currentSection);
        currentSection = null;
      }
      if (currentChapter) {
        chapters.push(currentChapter);
      }

      // 새 챕터 시작
      const chapterNumber = chapters.length + 1;
      currentChapter = {
        number: chapterNumber,
        title: line,
        content: '',
        sections: [],
        learningObjectives: [],
      };
    }
    // 섹션 제목 감지
    else if (sectionPattern.test(line) && currentChapter) {
      // 이전 섹션 저장
      if (currentSection && contentBuffer.length > 0) {
        currentSection.content = contentBuffer.join('\n\n');
        contentBuffer = [];
      }
      if (currentSection) {
        currentChapter.sections.push(currentSection);
      }

      // 새 섹션 시작
      currentSection = {
        title: line,
        content: '',
        order: currentChapter.sections.length,
      };
    }
    // 학습 목표 감지
    else if (line.includes('학습목표') || line.includes('학습 목표')) {
      if (currentChapter && contentBuffer.length > 0) {
        currentChapter.learningObjectives = extractLearningObjectives(contentBuffer);
        contentBuffer = [];
      }
    }
    // 일반 내용
    else {
      contentBuffer.push(line);
    }
  }

  // 마지막 챕터/섹션 저장
  if (currentSection && contentBuffer.length > 0) {
    currentSection.content = contentBuffer.join('\n\n');
  }
  if (currentChapter && currentSection) {
    currentChapter.sections.push(currentSection);
  }
  if (currentChapter) {
    if (contentBuffer.length > 0 && !currentSection) {
      currentChapter.content = contentBuffer.join('\n\n');
    }
    chapters.push(currentChapter);
  }

  return chapters;
}

/**
 * 학습 목표 추출
 */
function extractLearningObjectives(lines) {
  const objectives = [];
  const bulletPattern = /^[•\-\*\d+\.)]/;

  for (const line of lines) {
    if (bulletPattern.test(line.trim())) {
      objectives.push(line.replace(bulletPattern, '').trim());
    }
  }

  return objectives.length > 0 ? objectives : ['학습 목표를 추가하세요'];
}

/**
 * PDF를 교재 데이터 구조로 변환
 */
export async function convertPDFToTextbook(filePath, metadata = {}) {
  try {
    // PDF에서 텍스트 추출
    const { text, numPages, info } = await extractTextFromPDF(filePath);

    // 내용 구조화
    const chapters = structurePDFContent(text);

    // 교재 메타데이터 생성
    const textbookData = {
      title: metadata.title || info.Title || '제목 없음',
      subtitle: metadata.subtitle || '',
      description: metadata.description || `${numPages}페이지의 교육 자료`,
      author: metadata.author || info.Author || '저자 미상',
      language: metadata.language || 'ko',
      metadata: {
        subject: metadata.subject || info.Subject || '일반',
        targetAudience: metadata.targetAudience || '일반',
        difficulty: metadata.difficulty || 'intermediate',
        keywords: metadata.keywords || [],
        source: {
          type: 'pdf',
          pages: numPages,
          originalInfo: info,
        },
      },
      chapters: chapters.map((chapter, index) => ({
        number: chapter.number,
        title: chapter.title,
        content: chapter.content || chapter.sections.map(s => s.content).join('\n\n'),
        learningObjectives: chapter.learningObjectives.length > 0
          ? chapter.learningObjectives
          : ['학습 목표를 추가하세요'],
        summary: generateChapterSummary(chapter),
        order: index,
        sections: chapter.sections,
      })),
    };

    return textbookData;
  } catch (error) {
    console.error('PDF 변환 오류:', error);
    throw error;
  }
}

/**
 * 챕터 요약 생성 (간단한 버전)
 */
function generateChapterSummary(chapter) {
  const contentPreview = chapter.content
    ? chapter.content.substring(0, 200)
    : chapter.sections[0]?.content.substring(0, 200) || '';

  return contentPreview + (contentPreview.length >= 200 ? '...' : '');
}
