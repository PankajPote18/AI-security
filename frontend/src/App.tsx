import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from '@/auth/RequireAuth'
import { AppShell } from '@/components/AppShell'
import { AnalysisPage } from '@/pages/AnalysisPage'
import { AnalyzePage } from '@/pages/AnalyzePage'
import { HistoryPage } from '@/pages/HistoryPage'
import { LoginPage } from '@/pages/LoginPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/analyses/:id" element={<AnalysisPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/" element={<Navigate to="/analyze" replace />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
