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
  login: (email, password, nativeLanguage, learningLanguage, proficiencyLevel) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, nativeLanguage, learningLanguage, proficiencyLevel })
    }),

  signup: (username, email, password, nativeLanguage, learningLanguage, proficiencyLevel) =>
    request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, nativeLanguage, learningLanguage, proficiencyLevel })
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

  sendChatMessage: (message, audioSpeed = 0.8) =>
    request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message, audio_speed: audioSpeed })
    }),

  getChatHistory: () => request('/chat/history'),

  startNewChatSession: () =>
    request('/chat/new-session', {
      method: 'POST'
    }),

  regenerateAudio: (text, language, audioSpeed = 0.8) =>
    request('/chat/regenerate-audio', {
      method: 'POST',
      body: JSON.stringify({ text, language, audio_speed: audioSpeed })
    }),

    async transcribeAudio(audioBlob, language = null) {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  if (language) {
    formData.append('language', language)
  }

  const token = getToken()

  const response = await fetch(`${API_BASE}/chat/transcribe`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Failed to transcribe audio')
  }

  return response.json()
}
}

//     async transcribeAudio(audioBlob, language = null) {
//     const formData = new FormData()
//     formData.append('audio', audioBlob, 'recording.webm')
//     if (language) {
//       formData.append('language', language)
//     }

//     const response = await fetch(`${API_BASE_URL}/chat/transcribe`, {
//       method: 'POST',
//       headers: {
//         'Authorization': `Bearer ${getAuthToken()}`
//       },
//       body: formData
//     })

//     if (!response.ok) {
//       const error = await response.json()
//       throw new Error(error.message || 'Failed to transcribe audio')
//     }

//     return response.json()
//   }

// }