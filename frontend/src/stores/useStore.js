import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useStore = create(
  persist(
    (set, get) => ({
      // Auth state
      token: null,
      user: null,
      isAuthenticated: false,
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),

      // Research state
      currentResearch: null,
      researchProgress: 0,
      researchStatus: 'idle', // idle | running | completed | failed
      setCurrentResearch: (research) => set({ currentResearch: research }),
      setResearchProgress: (progress) => set({ researchProgress: progress }),
      setResearchStatus: (status) => set({ researchStatus: status }),
      resetResearch: () => set({ currentResearch: null, researchProgress: 0, researchStatus: 'idle' }),

      // UI state
      darkMode: false,
      sidebarOpen: true,
      apiBaseUrl: 'http://localhost:8000',
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setApiBaseUrl: (url) => set({ apiBaseUrl: url }),

      // Data cache
      reports: [],
      documents: [],
      entities: [],
      setReports: (reports) => set({ reports }),
      setDocuments: (documents) => set({ documents }),
      setEntities: (entities) => set({ entities }),
    }),
    {
      name: 'deep-research-agent-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        darkMode: state.darkMode,
        apiBaseUrl: state.apiBaseUrl,
      }),
    }
  )
)
