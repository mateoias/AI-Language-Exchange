import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('token')
    if (token) {
      api.getProfile()
        .then(userData => setUser(userData))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }

    // Auto-logout on page unload
    const handleBeforeUnload = () => {
      localStorage.removeItem('token')
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [])

  const login = async (email, password, nativeLanguage, learningLanguage) => {
    const response = await api.login(email, password, nativeLanguage, learningLanguage)
    localStorage.setItem('token', response.token)
    setUser(response.user)
    return response
  }

  const signup = async (username, email, password, nativeLanguage, learningLanguage) => {
    const response = await api.signup(username, email, password, nativeLanguage, learningLanguage)
    localStorage.setItem('token', response.token)
    setUser(response.user)
    return response
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  const updatePersonalization = async (data) => {
    const response = await api.updatePersonalization(data)
    setUser(response.user)
    return response
  }

  const deletePersonalization = async () => {
    const response = await api.deletePersonalization()
    setUser(response.user)
    return response
  }

  const value = {
    user,
    login,
    signup,
    logout,
    updatePersonalization,
    deletePersonalization,
    loading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}