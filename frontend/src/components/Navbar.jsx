import { useStore } from '../stores/useStore.js'
import { Menu, Sun, Moon, Search } from 'lucide-react'

export default function Navbar() {
  const { toggleSidebar, darkMode, toggleDarkMode, user } = useStore()

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 lg:px-6">
      <button
        onClick={toggleSidebar}
        className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      <div className="ml-4 flex items-center text-gray-400 dark:text-gray-500">
        <Search className="w-4 h-4" />
        <span className="ml-2 text-sm hidden sm:inline">Deep Research Agent</span>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          aria-label="Toggle theme"
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {user && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-700 dark:text-primary-300 font-semibold text-sm">
              {user.name?.charAt(0)?.toUpperCase() || user.email?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden md:block">
              {user.name || user.email}
            </span>
          </div>
        )}
      </div>
    </header>
  )
}
