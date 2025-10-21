import jwt from 'jsonwebtoken';

/**
 * JWT 인증 미들웨어
 */
export function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({ error: '인증 토큰이 필요합니다.' });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: '유효하지 않은 토큰입니다.' });
    }
    req.user = user;
    next();
  });
}

/**
 * 교수 권한 확인 미들웨어
 */
export function requireProfessor(req, res, next) {
  if (req.user.role !== 'professor') {
    return res.status(403).json({ error: '교수 권한이 필요합니다.' });
  }
  next();
}

/**
 * 학생 권한 확인 미들웨어
 */
export function requireStudent(req, res, next) {
  if (req.user.role !== 'student') {
    return res.status(403).json({ error: '학생 권한이 필요합니다.' });
  }
  next();
}
