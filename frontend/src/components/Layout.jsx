import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { useStore } from '../stores/useStore.js'
import Navbar from './Navbar.jsx'
import {
  LayoutDashboard,
  Search,
  FileText,
  Network,
  Settings,
  Menu,
  X,
  LogOut,
} from 'lucide-react'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/research', label: 'Research', icon: Search },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/graphs', label: 'Graphs', icon: Network },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout() {
  const { sidebarOpen, toggleSidebar, darkMode, logout } = useStore()
  const location = useLocation()

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-200 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-20 xl:w-64'
        }`}
      >
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
            <Search className="w-6 h-6 text-primary-600 dark:text-primary-400 flex-shrink-0" />
            <span className={`ml-3 font-bold text-lg text-gray-900 dark:text-white whitespace-nowrap transition-opacity ${!sidebarOpen ? 'lg:hidden xl:inline' : ''}`}>
              Deep Research
            </span>
          </div>

          {/* Nav items */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <a
                  key={item.path}
                  href={item.path}
                  className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className={`ml-3 whitespace-nowrap transition-opacity ${!sidebarOpen ? 'lg:hidden xl:inline' : ''}`}>
                    {item.label}
                  </span>
                </a>
              )
            })}
          </nav>

          {/* Bottom actions */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={logout}
              className="flex items-center w-full px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <LogOut className="w-5 h-5 flex-shrink-0" />
              <span className={`ml-3 whitespace-nowrap transition-opacity ${!sidebarOpen ? 'lg:hidden xl:inline' : ''}`}>
                Logout
              </span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
