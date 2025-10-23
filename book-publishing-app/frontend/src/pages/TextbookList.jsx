import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  IconButton,
  TextField,
  InputAdornment,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import SearchIcon from '@mui/icons-material/Search';
import { textbookAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';
import { format } from 'date-fns';

const statusColors = {
  DRAFT: 'default',
  IN_REVIEW: 'info',
  APPROVED: 'success',
  PUBLISHED: 'primary',
  ARCHIVED: 'secondary',
};

const statusLabels = {
  DRAFT: '초안',
  IN_REVIEW: '검토 중',
  APPROVED: '승인됨',
  PUBLISHED: '출판됨',
  ARCHIVED: '보관됨',
};

function TextbookList() {
  const navigate = useNavigate();
  const { isEditor } = useAuthStore();
  const [search, setSearch] = useState('');

  const { data, isLoading, error } = useQuery(
    ['textbooks', { search }],
    () => textbookAPI.getAll({ search }),
    {
      keepPreviousData: true,
    }
  );

  if (isLoading) {
    return (
      <Box className="loading-container">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box className="error-container">
        <Typography variant="h6" color="error">
          오류가 발생했습니다
        </Typography>
        <Typography variant="body2">{error.message}</Typography>
      </Box>
    );
  }

  const textbooks = data?.data || [];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">교재 관리</Typography>
        {isEditor() && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/textbooks/new')}
          >
            새 교재 생성
          </Button>
        )}
      </Box>

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="교재 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>제목</TableCell>
              <TableCell>저자</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>언어</TableCell>
              <TableCell>생성일</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {textbooks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary">
                    교재가 없습니다
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              textbooks.map((textbook) => (
                <TableRow key={textbook.id} hover>
                  <TableCell>
                    <Typography variant="body1">{textbook.title}</Typography>
                    {textbook.subtitle && (
                      <Typography variant="caption" color="text.secondary">
                        {textbook.subtitle}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{textbook.author}</TableCell>
                  <TableCell>
                    <Chip
                      label={statusLabels[textbook.status]}
                      color={statusColors[textbook.status]}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{textbook.language.toUpperCase()}</TableCell>
                  <TableCell>
                    {format(new Date(textbook.createdAt), 'yyyy-MM-dd')}
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/textbooks/${textbook.id}`)}
                      title="보기"
                    >
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                    {isEditor() && (
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/textbooks/${textbook.id}/edit`)}
                        title="편집"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
}

export default TextbookList;
