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

function Register() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();

  const password = watch('password');

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      setError('');

      const { confirmPassword, ...registerData } = data;
      const response = await authAPI.register(registerData);

      if (response.success) {
        toast.success('회원가입 성공! 로그인 페이지로 이동합니다.');
        navigate('/login');
      } else {
        setError(response.error || '회원가입에 실패했습니다.');
      }
    } catch (err) {
      setError(err.response?.data?.error || '회원가입 중 오류가 발생했습니다.');
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
            회원가입
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
              id="name"
              label="이름"
              name="name"
              autoComplete="name"
              autoFocus
              {...register('name', {
                required: '이름을 입력하세요',
                minLength: {
                  value: 2,
                  message: '이름은 최소 2자 이상이어야 합니다',
                },
              })}
              error={!!errors.name}
              helperText={errors.name?.message}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="이메일"
              name="email"
              autoComplete="email"
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
              autoComplete="new-password"
              {...register('password', {
                required: '비밀번호를 입력하세요',
                minLength: {
                  value: 8,
                  message: '비밀번호는 최소 8자 이상이어야 합니다',
                },
                pattern: {
                  value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                  message: '대문자, 소문자, 숫자를 포함해야 합니다',
                },
              })}
              error={!!errors.password}
              helperText={errors.password?.message}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="비밀번호 확인"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              {...register('confirmPassword', {
                required: '비밀번호 확인을 입력하세요',
                validate: (value) => value === password || '비밀번호가 일치하지 않습니다',
              })}
              error={!!errors.confirmPassword}
              helperText={errors.confirmPassword?.message}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : '회원가입'}
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link component={RouterLink} to="/login" variant="body2">
                이미 계정이 있으신가요? 로그인
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default Register;
