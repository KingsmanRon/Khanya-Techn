/**
 * MTP Dashboard - Main Application
 * Machine Trust Protocol Frontend
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Layout
import Layout from './components/layout/Layout';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AgentList from './pages/agents/AgentList';
import AgentDetail from './pages/agents/AgentDetail';
import AgentForm from './pages/agents/AgentForm';
import Audit from './pages/Audit';
import Trust from './pages/Trust';
import Certifications from './pages/Certifications';
import Disputes from './pages/Disputes';
import Blockchain from './pages/Blockchain';
import Settings from './pages/Settings';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Route */}
            <Route path="/login" element={<Login />} />

            {/* Protected Routes */}
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="agents" element={<AgentList />} />
              <Route path="agents/new" element={<AgentForm />} />
              <Route path="agents/:id" element={<AgentDetail />} />
              <Route path="audit" element={<Audit />} />
              <Route path="trust" element={<Trust />} />
              <Route path="certifications" element={<Certifications />} />
              <Route path="disputes" element={<Disputes />} />
              <Route path="blockchain" element={<Blockchain />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
