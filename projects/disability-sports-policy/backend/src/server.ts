import express, { Express } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { initializeDatabases, closeDatabases } from './config/database';

// Routes
import templateRoutes from './routes/template.routes';
import ragRoutes from './routes/rag.routes';
import documentRoutes from './routes/document.routes';
import analysisRoutes from './routes/analysis.routes';

dotenv.config();

const app: Express = express();
const PORT = process.env.PORT || 5000;

// ============================================================================
// Middleware
// ============================================================================
app.use(helmet()); // 보안 헤더
app.use(cors()); // CORS 허용
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// ============================================================================
// Routes
// ============================================================================
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
});

app.use('/api/templates', templateRoutes);
app.use('/api/rag', ragRoutes);
app.use('/api/documents', documentRoutes);
app.use('/api/analysis', analysisRoutes);

// ============================================================================
// Error Handling
// ============================================================================
app.use(
  (
    err: Error,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction
  ) => {
    console.error('[Server Error]', err);
    res.status(500).json({
      success: false,
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: err.message || '서버 오류가 발생했습니다.',
      },
    });
  }
);

// ============================================================================
// Server Start
// ============================================================================
async function startServer() {
  try {
    // 데이터베이스 초기화
    await initializeDatabases();

    // 서버 시작
    app.listen(PORT, () => {
      console.log(`
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🚀 범용 정책 분석 플랫폼 서버 시작                        ║
║                                                            ║
║   📍 서버 주소: http://localhost:${PORT}
║   🌐 환경: ${process.env.NODE_ENV || 'development'}                              ║
║   📊 API 버전: ${process.env.API_VERSION || 'v1'}                                ║
║                                                            ║
║   6계층 아키텍처:                                            ║
║   ├─ Layer 1: 데이터 수집 (크롤링)                          ║
║   ├─ Layer 2: 데이터 저장 (PostgreSQL + MongoDB + Qdrant) ║
║   ├─ Layer 3: NLP 처리 (텍스트 분석)                        ║
║   ├─ Layer 4: AI 분석 (Claude API + RAG)                  ║
║   ├─ Layer 5: API (Express.js)                           ║
║   └─ Layer 6: 프론트엔드 (React)                            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
      `);
    });

    // Graceful Shutdown
    process.on('SIGTERM', async () => {
      console.log('SIGTERM 신호 수신: 서버 종료 중...');
      await closeDatabases();
      process.exit(0);
    });

    process.on('SIGINT', async () => {
      console.log('\nSIGINT 신호 수신: 서버 종료 중...');
      await closeDatabases();
      process.exit(0);
    });
  } catch (error) {
    console.error('❌ 서버 시작 실패:', error);
    process.exit(1);
  }
}

startServer();

export default app;
