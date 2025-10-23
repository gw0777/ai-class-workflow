import { Container, Typography, Grid, Paper, Box } from '@mui/material';
import BookIcon from '@mui/icons-material/Book';
import GavelIcon from '@mui/icons-material/Gavel';
import PeopleIcon from '@mui/icons-material/People';
import { useAuthStore } from '../store/authStore';

function Dashboard() {
  const { user } = useAuthStore();

  const stats = [
    { title: '총 교재', value: '12', icon: <BookIcon sx={{ fontSize: 40 }} />, color: '#1976d2' },
    { title: '출판 규정', value: '8', icon: <GavelIcon sx={{ fontSize: 40 }} />, color: '#dc004e' },
    { title: '사용자', value: '24', icon: <PeopleIcon sx={{ fontSize: 40 }} />, color: '#2e7d32' },
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          대시보드
        </Typography>
        <Typography variant="body1" color="text.secondary">
          안녕하세요, {user?.name}님 ({user?.role})
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Paper
              elevation={2}
              sx={{
                p: 3,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: 150,
              }}
            >
              <Box sx={{ color: stat.color, mb: 1 }}>{stat.icon}</Box>
              <Typography variant="h4" gutterBottom>
                {stat.value}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stat.title}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4 }}>
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            최근 활동
          </Typography>
          <Typography variant="body2" color="text.secondary">
            최근 활동 내역이 여기에 표시됩니다.
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
}

export default Dashboard;
