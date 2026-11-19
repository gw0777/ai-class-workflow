import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 데이터베이스 시드 시작...');

  // 1. 관리자 사용자 생성
  console.log('👤 관리자 계정 생성 중...');
  const adminPassword = await bcrypt.hash('Admin123!', 10);
  const admin = await prisma.user.upsert({
    where: { email: 'admin@bookpublishing.com' },
    update: {},
    create: {
      email: 'admin@bookpublishing.com',
      password: adminPassword,
      name: '시스템 관리자',
      role: 'ADMIN'
    }
  });
  console.log(`✅ 관리자 생성 완료: ${admin.email}`);

  // 2. 샘플 편집자 생성
  console.log('👥 샘플 사용자 생성 중...');
  const editorPassword = await bcrypt.hash('Editor123!', 10);
  const editor = await prisma.user.upsert({
    where: { email: 'editor@bookpublishing.com' },
    update: {},
    create: {
      email: 'editor@bookpublishing.com',
      password: editorPassword,
      name: '김편집',
      role: 'EDITOR'
    }
  });

  const reviewerPassword = await bcrypt.hash('Reviewer123!', 10);
  const reviewer = await prisma.user.upsert({
    where: { email: 'reviewer@bookpublishing.com' },
    update: {},
    create: {
      email: 'reviewer@bookpublishing.com',
      password: reviewerPassword,
      name: '이검토',
      role: 'REVIEWER'
    }
  });
  console.log(`✅ 샘플 사용자 생성 완료`);

  // 3. 출판 규정 생성
  console.log('📋 출판 규정 생성 중...');
  const regulations = await Promise.all([
    prisma.publishingRegulation.create({
      data: {
        title: '저작권법 기본 원칙',
        description: '대한민국 저작권법에 따른 교재 출판 시 저작권 준수 사항',
        content: `교재 출판 시 저작권 관련 필수 준수사항:

1. 저작자의 허락 없이 타인의 저작물을 무단으로 복제, 배포할 수 없습니다.
2. 인용의 경우 정당한 범위 내에서 출처를 명시해야 합니다.
3. 교육 목적이라도 상업적 이용 시 저작권자의 동의가 필요합니다.
4. 공공누리 등 공공저작물의 경우 이용 조건을 확인해야 합니다.`,
        category: 'COPYRIGHT',
        country: 'KR',
        version: '1.0',
        effectiveDate: new Date('2024-01-01'),
        source: 'https://www.copyright.or.kr',
        tags: ['저작권', '법률', '필수']
      }
    }),
    prisma.publishingRegulation.create({
      data: {
        title: 'ISBN 등록 절차',
        description: 'ISBN 발급 및 등록 절차 안내',
        content: `ISBN 등록 절차:

1. 국립중앙도서관 ISBN 센터 접속
2. 출판사 등록 (최초 1회)
3. 도서 정보 입력
4. ISBN 발급 신청
5. 승인 후 ISBN 부여
6. 교재에 ISBN 표기`,
        category: 'ISBN',
        country: 'KR',
        version: '1.0',
        effectiveDate: new Date('2024-01-01'),
        source: 'https://seoji.nl.go.kr',
        tags: ['ISBN', 'registration', '필수']
      }
    }),
    prisma.publishingRegulation.create({
      data: {
        title: '교재 편집 표준 형식',
        description: '교재 편집 시 준수해야 할 표준 형식',
        content: `교재 편집 표준 형식:

1. 판형: A4 (210mm × 297mm) 또는 B5 (182mm × 257mm)
2. 여백: 상하좌우 각 20mm 이상
3. 글꼴: 본문 10~11pt, 제목 14~18pt
4. 줄간격: 160~180%
5. 페이지 번호: 하단 중앙 또는 외곽
6. 목차, 색인 포함 권장`,
        category: 'FORMATTING',
        country: 'KR',
        version: '1.0',
        effectiveDate: new Date('2024-01-01'),
        tags: ['편집', '형식', '표준']
      }
    }),
    prisma.publishingRegulation.create({
      data: {
        title: '교육 콘텐츠 품질 기준',
        description: '교육용 교재의 콘텐츠 품질 기준',
        content: `교육 콘텐츠 품질 기준:

1. 학습 목표의 명확한 제시
2. 체계적인 내용 구성
3. 적절한 예시와 실습 문제 포함
4. 최신 정보 반영
5. 정확한 용어 사용
6. 평가 문항의 타당성 확보
7. 다양한 난이도 구성`,
        category: 'CONTENT_STANDARD',
        country: 'KR',
        version: '1.0',
        effectiveDate: new Date('2024-01-01'),
        tags: ['품질', '교육', '기준']
      }
    })
  ]);
  console.log(`✅ ${regulations.length}개 출판 규정 생성 완료`);

  // 4. 샘플 교재 생성
  console.log('📚 샘플 교재 생성 중...');
  const textbook = await prisma.textbook.create({
    data: {
      title: '스포츠 교육학 기초',
      subtitle: '체육 교사를 위한 필수 이론',
      description: '체육 교사와 스포츠 지도자를 위한 체육 교육학의 기초 이론을 다룹니다.',
      author: '김체육',
      language: 'ko',
      status: 'DRAFT',
      editorId: editor.id,
      metadata: {
        create: {
          subject: '체육교육',
          targetAudience: '예비 체육교사, 스포츠 지도자',
          difficulty: 'intermediate',
          keywords: ['체육', '교육학', '스포츠', '교수법']
        }
      }
    }
  });

  // 5. 샘플 챕터 생성
  console.log('📖 샘플 챕터 생성 중...');
  const chapter1 = await prisma.chapter.create({
    data: {
      textbookId: textbook.id,
      number: 1,
      title: '체육 교육학의 이해',
      content: `# 체육 교육학의 이해

체육 교육학은 체육 수업의 목표 설정, 내용 선정, 교수 방법, 평가 등을 연구하는 학문입니다.

## 1.1 체육 교육학의 정의

체육 교육학은 체육을 가르치고 배우는 과정에서 발생하는 다양한 현상을 과학적으로 탐구하는 학문입니다.

## 1.2 체육 교육의 목표

1. 신체적 발달
2. 정서적 안정
3. 사회성 함양
4. 인지적 성장`,
      learningObjectives: [
        '체육 교육학의 개념을 설명할 수 있다',
        '체육 교육의 목표를 이해하고 설명할 수 있다',
        '체육 교육학의 필요성을 설명할 수 있다'
      ],
      summary: '이 장에서는 체육 교육학의 기본 개념과 목표를 학습합니다.',
      order: 1
    }
  });

  const chapter2 = await prisma.chapter.create({
    data: {
      textbookId: textbook.id,
      number: 2,
      title: '직접교수 모형',
      content: `# 직접교수 모형

직접교수 모형은 교사 중심의 체계적인 교수 방법으로, 명확한 학습 목표와 단계별 지도가 특징입니다.

## 2.1 직접교수 모형의 특징

1. 명확한 학습 목표 제시
2. 단계별 설명과 시범
3. 즉각적인 피드백
4. 충분한 연습 시간 제공

## 2.2 수업 단계

1. 도입 (Set Induction)
2. 설명 및 시범 (Explanation & Demonstration)
3. 연습 (Practice)
4. 피드백 (Feedback)
5. 정리 (Closure)`,
      learningObjectives: [
        '직접교수 모형의 특징을 설명할 수 있다',
        '직접교수 모형의 수업 단계를 이해하고 적용할 수 있다',
        '효과적인 피드백 방법을 설명할 수 있다'
      ],
      summary: '직접교수 모형의 개념과 수업 단계를 학습합니다.',
      order: 2
    }
  });

  // 6. 샘플 평가 문항 생성
  console.log('✏️ 샘플 평가 문항 생성 중...');
  await Promise.all([
    prisma.assessment.create({
      data: {
        chapterId: chapter1.id,
        question: '체육 교육학의 주요 연구 대상이 아닌 것은?',
        type: 'MULTIPLE_CHOICE',
        options: [
          '교수 방법',
          '평가 방법',
          '학생 선수 스카우트',
          '체육 교육과정'
        ],
        answer: '학생 선수 스카우트',
        explanation: '체육 교육학은 교수-학습 과정을 연구하는 학문으로, 선수 스카우트는 스포츠 경영학의 영역입니다.',
        difficulty: 2,
        points: 1
      }
    }),
    prisma.assessment.create({
      data: {
        chapterId: chapter1.id,
        question: '체육 교육의 목표에는 신체적 발달만 포함된다.',
        type: 'TRUE_FALSE',
        options: ['참', '거짓'],
        answer: '거짓',
        explanation: '체육 교육은 신체적 발달뿐만 아니라 정서적, 사회적, 인지적 발달을 모두 포함합니다.',
        difficulty: 1,
        points: 1
      }
    }),
    prisma.assessment.create({
      data: {
        chapterId: chapter2.id,
        question: '직접교수 모형의 수업 단계를 순서대로 나열하시오.',
        type: 'SHORT_ANSWER',
        options: [],
        answer: '도입 - 설명 및 시범 - 연습 - 피드백 - 정리',
        explanation: '직접교수 모형은 5단계로 구성되며, 순차적으로 진행됩니다.',
        difficulty: 3,
        points: 2
      }
    })
  ]);
  console.log(`✅ 평가 문항 생성 완료`);

  // 7. 샘플 템플릿 생성
  console.log('📄 샘플 템플릿 생성 중...');
  await prisma.template.create({
    data: {
      name: '기본 교재 템플릿',
      description: '일반적인 교재 구조를 위한 기본 템플릿',
      structure: {
        sections: [
          { name: '표지', required: true },
          { name: '목차', required: true },
          { name: '서문', required: false },
          { name: '본문', required: true },
          { name: '참고문헌', required: true },
          { name: '색인', required: false }
        ]
      },
      styles: {
        font: {
          title: 'Noto Sans KR',
          body: 'Noto Sans KR'
        },
        sizes: {
          title: '18pt',
          subtitle: '14pt',
          body: '10pt'
        },
        colors: {
          primary: '#1976d2',
          secondary: '#424242'
        }
      }
    }
  });
  console.log(`✅ 템플릿 생성 완료`);

  console.log('\n✨ 데이터베이스 시드 완료!\n');
  console.log('📝 생성된 계정 정보:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('👤 관리자');
  console.log('   이메일: admin@bookpublishing.com');
  console.log('   비밀번호: Admin123!');
  console.log('');
  console.log('👤 편집자');
  console.log('   이메일: editor@bookpublishing.com');
  console.log('   비밀번호: Editor123!');
  console.log('');
  console.log('👤 검토자');
  console.log('   이메일: reviewer@bookpublishing.com');
  console.log('   비밀번호: Reviewer123!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
}

main()
  .catch((e) => {
    console.error('❌ 시드 중 오류 발생:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
