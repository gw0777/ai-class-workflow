import { Container, Typography, Box, CircularProgress } from '@mui/material';

function TextbookDetail() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4">교재 상세</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          교재 상세 페이지 (구현 예정)
        </Typography>
      </Box>
    </Container>
  );
}

export default TextbookDetail;
