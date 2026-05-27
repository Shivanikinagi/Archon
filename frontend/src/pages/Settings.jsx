import { useState } from 'react'
import { useStore } from '../stores/useStore.js'
import { register } from '../services/api.js'
import {
  Settings as SettingsIcon,
  Globe,
  Sun,
  Moon,
  User,
  Mail,
  Key,
  Save,
  Loader2,
  CheckCircle,
} from 'lucide-react'

export default function Settings() {
  const {
    darkMode,
    toggleDarkMode,
    apiBaseUrl,
    setApiBaseUrl,
    user,
    setUser,
  } = useStore()

  const [apiUrl, setApiUrl] = useState(apiBaseUrl)
  const [name, setName] = useState(user?.name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')

  const handleSaveApi = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    setSaveMessage('')

    try {
      setApiBaseUrl(apiUrl)
      setSaveMessage('API endpoint saved successfully')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (err) {
      setSaveMessage('Failed to save settings')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    setSaveMessage('')

    try {
      setUser({ ...user, name, email })
      setSaveMessage('Profile updated successfully')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (err) {
      setSaveMessage('Failed to update profile')
    } finally {
      setIsSaving(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    setSaveMessage('')

    try {
      // In a real app, you'd call an API here
      setCurrentPassword('')
      setNewPassword('')
      setSaveMessage('Password changed successfully')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch (err) {
      setSaveMessage('Failed to change password')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Manage your preferences and account settings
        </p>
      </div>

      {saveMessage && (
        <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {saveMessage}
        </div>
      )}

      {/* Appearance */}
      <div className="card space-y-4">
        <div className="flex items-center gap-3">
          {darkMode ? (
            <Moon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          ) : (
            <Sun className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          )}
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Appearance</h2>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-900 dark:text-white">Dark Mode</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Toggle between light and dark themes
            </p>
          </div>
          <button
            onClick={toggleDarkMode}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              darkMode ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                darkMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* API Configuration */}
      <div className="card space-y-4">
        <div className="flex items-center gap-3">
          <Globe className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            API Configuration
          </h2>
        </div>

        <form onSubmit={handleSaveApi} className="space-y-4">
          <div>
            <label className="label">Backend API URL</label>
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="url"
                className="input pl-10"
                placeholder="http://localhost:8000"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                required
              />
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              The base URL of your Deep Research Agent backend API
            </p>
          </div>
          <button
            type="submit"
            disabled={isSaving}
            className="btn-primary disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save API Settings
              </>
            )}
          </button>
        </form>
      </div>

      {/* Profile */}
      <div className="card space-y-4">
        <div className="flex items-center gap-3">
          <User className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Profile</h2>
        </div>

        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div>
            <label className="label">Display Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                className="input pl-10"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="email"
                className="input pl-10"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={isSaving}
            className="btn-primary disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Update Profile
              </>
            )}
          </button>
        </form>
      </div>

      {/* Change Password */}
      <div className="card space-y-4">
        <div className="flex items-center gap-3">
          <Key className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Change Password
          </h2>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="label">Current Password</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">New Password</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={isSaving}
            className="btn-primary disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Changing...
              </>
            ) : (
              'Change Password'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
