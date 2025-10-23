import fs from 'fs/promises';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * PPTX 파일을 텍스트로 변환
 *
 * 참고: 이 기능은 LibreOffice가 시스템에 설치되어 있어야 합니다.
 * 실제 프로덕션에서는 더 강력한 라이브러리나 서비스를 사용하는 것이 좋습니다.
 */
export async function extractTextFromPPTX(filePath) {
  try {
    // PPTX는 ZIP 파일 형식이므로, 간단한 텍스트 추출을 위해
    // 슬라이드 내용을 파싱합니다.

    // 실제 구현에서는 node-pptx 또는 mammoth 같은 라이브러리 사용
    // 여기서는 간단한 구조를 반환

    const fileContent = await fs.readFile(filePath);

    return {
      slides: [],
      numSlides: 0,
      text: '(PPTX 변환 기능은 추가 라이브러리 설치가 필요합니다)',
      metadata: {
        fileName: filePath.split('/').pop(),
      },
    };
  } catch (error) {
    console.error('PPTX 텍스트 추출 오류:', error);
    throw new Error('PPTX 파일을 읽을 수 없습니다.');
  }
}

/**
 * PPTX 슬라이드를 챕터로 변환
 * 각 슬라이드 또는 슬라이드 그룹을 챕터로 매핑
 */
export function structurePPTXContent(slides) {
  const chapters = [];
  let currentChapter = null;
  let slideIndex = 0;

  for (const slide of slides) {
    // 제목 슬라이드나 섹션 구분 슬라이드를 챕터로 인식
    if (isChapterSlide(slide)) {
      if (currentChapter) {
        chapters.push(currentChapter);
      }

      currentChapter = {
        number: chapters.length + 1,
        title: slide.title || `챕터 ${chapters.length + 1}`,
        content: slide.content || '',
        sections: [],
        learningObjectives: extractObjectives(slide.content),
      };
    } else if (currentChapter) {
      // 일반 슬라이드를 섹션으로 추가
      currentChapter.sections.push({
        title: slide.title || `섹션 ${currentChapter.sections.length + 1}`,
        content: slide.content || '',
        order: currentChapter.sections.length,
      });
    }
    slideIndex++;
  }

  if (currentChapter) {
    chapters.push(currentChapter);
  }

  return chapters;
}

/**
 * 슬라이드가 챕터 시작인지 판단
 */
function isChapterSlide(slide) {
  const titlePatterns = [
    /^제?\s*\d+\s*장/,
    /^Chapter\s+\d+/i,
    /^챕터\s+\d+/,
  ];

  if (!slide.title) return false;

  return titlePatterns.some(pattern => pattern.test(slide.title));
}

/**
 * 학습 목표 추출
 */
function extractObjectives(content) {
  if (!content) return [];

  const lines = content.split('\n');
  const objectives = [];

  for (const line of lines) {
    if (line.includes('목표') || line.includes('objective')) {
      const bulletPattern = /^[•\-\*\d+\.)]/;
      if (bulletPattern.test(line.trim())) {
        objectives.push(line.replace(bulletPattern, '').trim());
      }
    }
  }

  return objectives.length > 0 ? objectives : ['학습 목표를 추가하세요'];
}

/**
 * PPTX를 교재 데이터 구조로 변환
 */
export async function convertPPTXToTextbook(filePath, metadata = {}) {
  try {
    // PPTX에서 슬라이드 추출
    const { slides, numSlides } = await extractTextFromPPTX(filePath);

    // 내용 구조화
    const chapters = structurePPTXContent(slides);

    // 교재 메타데이터 생성
    const textbookData = {
      title: metadata.title || '제목 없음',
      subtitle: metadata.subtitle || '',
      description: metadata.description || `${numSlides}개 슬라이드의 교육 자료`,
      author: metadata.author || '저자 미상',
      language: metadata.language || 'ko',
      metadata: {
        subject: metadata.subject || '일반',
        targetAudience: metadata.targetAudience || '일반',
        difficulty: metadata.difficulty || 'intermediate',
        keywords: metadata.keywords || [],
        source: {
          type: 'pptx',
          slides: numSlides,
        },
      },
      chapters: chapters.map((chapter, index) => ({
        number: chapter.number,
        title: chapter.title,
        content: chapter.content || chapter.sections.map(s => s.content).join('\n\n'),
        learningObjectives: chapter.learningObjectives,
        summary: chapter.content.substring(0, 200) || '요약을 추가하세요',
        order: index,
        sections: chapter.sections,
      })),
    };

    return textbookData;
  } catch (error) {
    console.error('PPTX 변환 오류:', error);
    throw error;
  }
}
