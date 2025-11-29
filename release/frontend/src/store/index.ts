import { create } from 'zustand'

interface User {
  id: number
  username: string
  email: string
  role: string
}

interface Team {
  id: number
  name: string
  description?: string
  account_id: string
  is_active: boolean
  member_count: number
  max_seats: number
  token_expires_at?: string
  created_at: string
}

type ThemeMode = 'light' | 'dark'

interface AppState {
  user: User | null
  teams: Team[]
  currentTeam: Team | null
  theme: ThemeMode
  setUser: (user: User | null) => void
  setTeams: (teams: Team[]) => void
  setCurrentTeam: (team: Team | null) => void
  setTheme: (theme: ThemeMode) => void
  toggleTheme: () => void
  logout: () => void
}

const getInitialTheme = (): ThemeMode => {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark' || saved === 'light') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useStore = create<AppState>((set, get) => ({
  user: null,
  teams: [],
  currentTeam: null,
  theme: getInitialTheme(),
  setUser: (user) => set({ user }),
  setTeams: (teams) => set({ teams }),
  setCurrentTeam: (team) => set({ currentTeam: team }),
  setTheme: (theme) => {
    localStorage.setItem('theme', theme)
    set({ theme })
  },
  toggleTheme: () => {
    const newTheme = get().theme === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', newTheme)
    set({ theme: newTheme })
  },
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, teams: [], currentTeam: null })
  },
}))
