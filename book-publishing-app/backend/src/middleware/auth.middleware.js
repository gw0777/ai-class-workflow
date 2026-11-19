import jwt from 'jsonwebtoken';

/**
 * JWT 토큰 인증 미들웨어
 */
export const authenticate = (req, res, next) => {
  try {
    // 헤더에서 토큰 추출
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: '인증 토큰이 제공되지 않았습니다.'
      });
    }

    const token = authHeader.substring(7); // 'Bearer ' 제거

    // 토큰 검증
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');

    // 사용자 정보를 request 객체에 추가
    req.user = {
      id: decoded.id,
      email: decoded.email,
      role: decoded.role
    };

    next();
  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        success: false,
        error: '유효하지 않은 토큰입니다.'
      });
    }

    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        error: '토큰이 만료되었습니다.'
      });
    }

    res.status(500).json({
      success: false,
      error: '인증 처리 중 오류가 발생했습니다.'
    });
  }
};

/**
 * 역할 기반 권한 확인 미들웨어
 */
export const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        error: '인증이 필요합니다.'
      });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: '접근 권한이 없습니다.',
        requiredRoles: roles,
        userRole: req.user.role
      });
    }

    next();
  };
};
