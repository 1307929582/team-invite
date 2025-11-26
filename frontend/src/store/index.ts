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
  created_at: string
}

interface AppState {
  user: User | null
  teams: Team[]
  currentTeam: Team | null
  setUser: (user: User | null) => void
  setTeams: (teams: Team[]) => void
  setCurrentTeam: (team: Team | null) => void
  logout: () => void
}

export const useStore = create<AppState>((set) => ({
  user: null,
  teams: [],
  currentTeam: null,
  setUser: (user) => set({ user }),
  setTeams: (teams) => set({ teams }),
  setCurrentTeam: (team) => set({ currentTeam: team }),
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, teams: [], currentTeam: null })
  },
}))
