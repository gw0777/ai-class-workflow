import { Container, Typography, Box } from '@mui/material';

function RegulationDetail() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4">출판 규정 상세</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          출판 규정 상세 페이지 (구현 예정)
        </Typography>
      </Box>
    </Container>
  );
}

export default RegulationDetail;
