import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../stores/useStore.js'
import { login, register } from '../services/api.js'
import { Search, Loader2 } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { setToken, setUser } = useStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isRegister, setIsRegister] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      if (isRegister) {
        // Register new user
        const registerResponse = await register({ email, password, name })
        if (registerResponse.user_id) {
          // After successful registration, log in
          const loginResponse = await login({ email, password })
          if (loginResponse.access_token) {
            setToken(loginResponse.access_token)
            setUser({ email, name })
            navigate('/dashboard')
          }
        }
      } else {
        // Login existing user
        const response = await login({ email, password })
        if (response.access_token) {
          setToken(response.access_token)
          setUser({ email })
          navigate('/dashboard')
        } else {
          setError('Invalid response from server')
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || (isRegister ? 'Registration failed' : 'Login failed. Please check your credentials.'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900 mb-4">
            <Search className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Deep Research Agent
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Sign in to access your research dashboard
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="label" htmlFor="name">Name</label>
                <input
                  id="name"
                  type="text"
                  className="input"
                  placeholder="Your Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required={isRegister}
                />
              </div>
            )}

            <div>
              <label className="label" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="label" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {isRegister ? 'Creating account...' : 'Signing in...'}
                </>
              ) : (
                isRegister ? 'Create Account' : 'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister)
                setError('')
              }}
              className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
            >
              {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
