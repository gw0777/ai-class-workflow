import { Container, Typography, Box } from '@mui/material';

function TextbookEditor() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4">교재 편집</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          교재 편집 페이지 (구현 예정)
        </Typography>
      </Box>
    </Container>
  );
}

export default TextbookEditor;
