import { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Link,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import { authAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';

function Login() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      setError('');

      const response = await authAPI.login(data);

      if (response.success) {
        setAuth(response.data.user, response.data.token);
        toast.success('로그인 성공!');
        navigate('/');
      } else {
        setError(response.error || '로그인에 실패했습니다.');
      }
    } catch (err) {
      setError(err.response?.data?.error || '로그인 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" gutterBottom>
            책 출판 관리 시스템
          </Typography>
          <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
            로그인
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="이메일"
              name="email"
              autoComplete="email"
              autoFocus
              {...register('email', {
                required: '이메일을 입력하세요',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: '유효한 이메일 주소를 입력하세요',
                },
              })}
              error={!!errors.email}
              helperText={errors.email?.message}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="비밀번호"
              type="password"
              id="password"
              autoComplete="current-password"
              {...register('password', {
                required: '비밀번호를 입력하세요',
              })}
              error={!!errors.password}
              helperText={errors.password?.message}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : '로그인'}
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link component={RouterLink} to="/register" variant="body2">
                계정이 없으신가요? 회원가입
              </Link>
            </Box>
          </Box>
        </Paper>

        <Box sx={{ mt: 4, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
          <Typography variant="caption" component="div" gutterBottom>
            <strong>테스트 계정:</strong>
          </Typography>
          <Typography variant="caption" component="div">
            관리자: admin@bookpublishing.com / Admin123!
          </Typography>
          <Typography variant="caption" component="div">
            편집자: editor@bookpublishing.com / Editor123!
          </Typography>
        </Box>
      </Box>
    </Container>
  );
}

export default Login;
