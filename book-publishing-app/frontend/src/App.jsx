import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import TextbookList from './pages/TextbookList';
import TextbookDetail from './pages/TextbookDetail';
import TextbookEditor from './pages/TextbookEditor';
import RegulationList from './pages/RegulationList';
import RegulationDetail from './pages/RegulationDetail';
import Profile from './pages/Profile';
import PrivateRoute from './components/PrivateRoute';
import { useAuthStore } from './store/authStore';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: [
      'Noto Sans KR',
      '-apple-system',
      'BlinkMacSystemFont',
      'Segoe UI',
      'Roboto',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
        <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/" />} />

        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="textbooks" element={<TextbookList />} />
          <Route path="textbooks/:id" element={<TextbookDetail />} />
          <Route path="textbooks/:id/edit" element={<TextbookEditor />} />
          <Route path="textbooks/new" element={<TextbookEditor />} />
          <Route path="regulations" element={<RegulationList />} />
          <Route path="regulations/:id" element={<RegulationDetail />} />
          <Route path="profile" element={<Profile />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App;
