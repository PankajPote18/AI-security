import { api } from './client'
import type {
  AnalysisMode,
  AnalysisOut,
  AnalysisSummaryOut,
  FeedbackOut,
  SecurityReportOut,
  TokenResponse,
  UserOut,
} from './types'

export const authApi = {
  register: (email: string, password: string) =>
    api.postNoAuth<UserOut>('/auth/register', { email, password }),
  login: (email: string, password: string) =>
    api.postNoAuth<TokenResponse>('/auth/login', { email, password }),
}

export const analysesApi = {
  analyze: (url: string, mode: AnalysisMode) =>
    api.post<AnalysisOut>('/analyze/url', { url }, { mode }),
  get: (id: string) => api.get<AnalysisOut>(`/analyses/${id}`),
  list: () => api.get<AnalysisSummaryOut[]>('/analyses'),
  report: {
    generate: (analysisId: string) => api.post<SecurityReportOut>(`/analyses/${analysisId}/report`),
    get: (analysisId: string) => api.get<SecurityReportOut>(`/analyses/${analysisId}/report`),
  },
  feedback: (analysisId: string, verdict: 'agree' | 'disagree', comment?: string) =>
    api.post<FeedbackOut>(`/analyses/${analysisId}/feedback`, { verdict, comment }),
}
