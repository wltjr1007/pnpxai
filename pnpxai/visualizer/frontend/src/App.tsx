// src/App.tsx
import React, { useEffect } from 'react';
import { HashRouter as Router } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme/theme';
import AppRoutes from './routes/AppRoutes';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './layouts/layout';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProjects } from './features/globalState';
import { RootState } from './app/store'; // Import the RootState type
import { useNavigate } from 'react-router-dom';

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppWithRouter />
      </Router>
    </ThemeProvider>
  );
};

export default App;

const AppWithRouter: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { error, loaded } = useSelector((state: RootState) => state.global);

  useEffect(() => {
    if (!loaded) {
      dispatch(fetchProjects() as any);
    }
  }, [dispatch, loaded]);

  useEffect(() => {
    if (error) {
      navigate('/not-found'); // Redirect to the Not Found page
    }
  }, [error, navigate]);

  return (
    <Layout>
      <AppRoutes />
    </Layout>
  );
};
