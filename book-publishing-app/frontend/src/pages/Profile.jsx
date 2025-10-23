import { Container, Typography, Box, Paper } from '@mui/material';
import { useAuthStore } from '../store/authStore';

function Profile() {
  const { user } = useAuthStore();

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4">프로필</Typography>
      </Box>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          사용자 정보
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1">
            <strong>이름:</strong> {user?.name}
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            <strong>이메일:</strong> {user?.email}
          </Typography>
          <Typography variant="body1" sx={{ mt: 1 }}>
            <strong>역할:</strong> {user?.role}
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}

export default Profile;
