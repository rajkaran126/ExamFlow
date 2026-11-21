// ============================================================
// EXAMFLOW – App Router & Entry
// ============================================================

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import LandingPage from './components/landing/LandingPage';
import AppShell from './components/layout/AppShell';
import { lazy, Suspense } from 'react';
import { Loader2 } from 'lucide-react';

// Lazy-load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Examinations = lazy(() => import('./pages/Examinations'));
const ExaminationDetail = lazy(() => import('./pages/Examinations/ExaminationDetail'));
const Candidates = lazy(() => import('./pages/Candidates'));
const CandidateDetail = lazy(() => import('./pages/Candidates/CandidateDetail'));
const Responses = lazy(() => import('./pages/Responses'));
const Evaluation = lazy(() => import('./pages/Evaluation'));
const Proctoring = lazy(() => import('./pages/Proctoring'));
const Normalisation = lazy(() => import('./pages/Normalisation'));
const Results = lazy(() => import('./pages/Results'));
const MeritList = lazy(() => import('./pages/MeritList'));
const ReEvaluation = lazy(() => import('./pages/ReEvaluation'));
const ExamflowAI = lazy(() => import('./pages/ExamflowAI'));
const Settings = lazy(() => import('./pages/Settings'));
const Login = lazy(() => import('./pages/Login'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-8 w-8 animate-spin text-[var(--ef-primary)]" />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Landing */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />

            {/* Application */}
            <Route path="/app" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="examinations" element={<Examinations />} />
              <Route path="examinations/:id" element={<ExaminationDetail />} />
              <Route path="candidates" element={<Candidates />} />
              <Route path="candidates/:id" element={<CandidateDetail />} />
              <Route path="responses" element={<Responses />} />
              <Route path="evaluation" element={<Evaluation />} />
              <Route path="proctoring" element={<Proctoring />} />
              <Route path="normalisation" element={<Normalisation />} />
              <Route path="results" element={<Results />} />
              <Route path="merit-list" element={<MeritList />} />
              <Route path="re-evaluation" element={<ReEvaluation />} />
              <Route path="ai" element={<ExamflowAI />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ThemeProvider>
  );
}
