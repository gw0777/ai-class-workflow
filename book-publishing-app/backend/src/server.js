import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import dotenv from 'dotenv';

// 라우트 임포트
import textbookRoutes from './routes/textbook.routes.js';
import regulationRoutes from './routes/regulation.routes.js';
import userRoutes from './routes/user.routes.js';
import workflowRoutes from './routes/workflow.routes.js';
import uploadRoutes from './routes/upload.routes.js';
import converterRoutes from './routes/converter.routes.js';

// 환경 변수 로드
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// 미들웨어
app.use(helmet()); // 보안 헤더
app.use(cors()); // CORS 설정
app.use(compression()); // 응답 압축
app.use(morgan('dev')); // HTTP 로깅
app.use(express.json({ limit: '10mb' })); // JSON 파싱
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 정적 파일 서빙
app.use('/uploads', express.static('uploads'));

// API 라우트
app.use('/api/textbooks', textbookRoutes);
app.use('/api/regulations', regulationRoutes);
app.use('/api/users', userRoutes);
app.use('/api/workflow', workflowRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/converter', converterRoutes);

// 헬스 체크 엔드포인트
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// 루트 엔드포인트
app.get('/', (req, res) => {
  res.json({
    message: '책 출판 관리 시스템 API',
    version: '1.0.0',
    endpoints: {
      textbooks: '/api/textbooks',
      regulations: '/api/regulations',
      users: '/api/users',
      workflow: '/api/workflow',
      upload: '/api/upload',
      converter: '/api/converter',
      health: '/health'
    }
  });
});

// 404 에러 핸들러
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: '요청한 리소스를 찾을 수 없습니다.',
    path: req.originalUrl
  });
});

// 글로벌 에러 핸들러
app.use((err, req, res, next) => {
  console.error(err.stack);

  res.status(err.status || 500).json({
    error: err.message || 'Internal Server Error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

// 서버 시작
app.listen(PORT, () => {
  console.log(`\n🚀 서버가 포트 ${PORT}에서 실행 중입니다.`);
  console.log(`📚 API 문서: http://localhost:${PORT}/`);
  console.log(`❤️  헬스 체크: http://localhost:${PORT}/health\n`);
});

// 프로세스 종료 처리
process.on('SIGTERM', () => {
  console.log('SIGTERM 신호 수신. 서버를 종료합니다...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\nSIGINT 신호 수신. 서버를 종료합니다...');
  process.exit(0);
});

export default app;
