const API_BASE = 'http://localhost:5000/api'

const getToken = () => localStorage.getItem('token')

const request = async (endpoint, options = {}) => {
  const token = getToken()
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    },
    ...options
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Something went wrong')
  }

  return data
}

export const api = {
  login: (email, password, nativeLanguage, learningLanguage) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, nativeLanguage, learningLanguage })
    }),

  signup: (username, email, password, nativeLanguage, learningLanguage) =>
    request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, nativeLanguage, learningLanguage })
    }),

  getProfile: () => request('/auth/profile'),

  updatePersonalization: (data) =>
    request('/user/personalization', {
      method: 'PUT',
      body: JSON.stringify(data)
    }),

  deletePersonalization: () =>
    request('/user/personalization', {
      method: 'DELETE'
    }),
    sendChatMessage: (message) =>
    request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message })
    }),
      getChatHistory: () => request('/chat/history'),

  startNewChatSession: () =>
    request('/chat/new-session', {
      method: 'POST'
    })
}