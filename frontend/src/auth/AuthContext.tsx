import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { clearToken, getToken, setToken as persistToken } from '@/api/client'

interface AuthContextValue {
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => getToken() !== null)

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated,
      login: (token: string) => {
        persistToken(token)
        setIsAuthenticated(true)
      },
      logout: () => {
        clearToken()
        setIsAuthenticated(false)
      },
    }),
    [isAuthenticated],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
