#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  책 출판 관리 시스템 백엔드 설정${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. .env 파일 확인
echo -e "${YELLOW}[1/5]${NC} 환경 변수 파일 확인 중..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다. .env.example을 복사합니다.${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env 파일이 생성되었습니다.${NC}"
    echo -e "${YELLOW}⚠️  .env 파일을 편집하여 데이터베이스 연결 정보를 입력하세요!${NC}"
else
    echo -e "${GREEN}✅ .env 파일이 존재합니다.${NC}"
fi
echo ""

# 2. 의존성 설치
echo -e "${YELLOW}[2/5]${NC} npm 패키지 설치 중..."
npm install
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ npm 패키지 설치 완료${NC}"
else
    echo -e "${RED}❌ npm 패키지 설치 실패${NC}"
    exit 1
fi
echo ""

# 3. Prisma 클라이언트 생성
echo -e "${YELLOW}[3/5]${NC} Prisma 클라이언트 생성 중..."
npx prisma generate
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Prisma 클라이언트 생성 완료${NC}"
else
    echo -e "${RED}❌ Prisma 클라이언트 생성 실패${NC}"
    exit 1
fi
echo ""

# 4. 데이터베이스 마이그레이션
echo -e "${YELLOW}[4/5]${NC} 데이터베이스 마이그레이션 실행 중..."
echo -e "${YELLOW}⚠️  데이터베이스가 준비되어 있는지 확인하세요.${NC}"
read -p "마이그레이션을 진행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npx prisma migrate dev --name init
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 데이터베이스 마이그레이션 완료${NC}"
    else
        echo -e "${RED}❌ 데이터베이스 마이그레이션 실패${NC}"
        echo -e "${YELLOW}💡 .env 파일의 DATABASE_URL을 확인하세요.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  마이그레이션을 건너뜁니다.${NC}"
fi
echo ""

# 5. 시드 데이터 생성
echo -e "${YELLOW}[5/5]${NC} 초기 데이터 생성..."
read -p "샘플 데이터를 생성하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run seed
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 초기 데이터 생성 완료${NC}"
    else
        echo -e "${RED}❌ 초기 데이터 생성 실패${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  시드 데이터 생성을 건너뜁니다.${NC}"
fi
echo ""

# 완료 메시지
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ 설정이 완료되었습니다!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}다음 명령어로 서버를 시작할 수 있습니다:${NC}"
echo -e "${YELLOW}  npm run dev${NC}    # 개발 모드로 서버 시작"
echo -e "${YELLOW}  npm start${NC}      # 프로덕션 모드로 서버 시작"
echo ""
echo -e "${BLUE}유용한 명령어:${NC}"
echo -e "${YELLOW}  npm run studio${NC}  # Prisma Studio로 데이터 관리"
echo -e "${YELLOW}  npm run seed${NC}    # 시드 데이터 재생성"
echo ""
