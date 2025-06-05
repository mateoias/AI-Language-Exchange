import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link, useNavigate } from 'react-router-dom'

const LANGUAGES = [
  'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 
  'Russian', 'Chinese', 'Japanese', 'Korean', 'Arabic', 'Hindi'
]

function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    nativeLanguage: '',
    learningLanguage: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  // Pre-populate language settings if user has them from previous session
  useEffect(() => {
    const savedNativeLanguage = localStorage.getItem('nativeLanguage')
    const savedLearningLanguage = localStorage.getItem('learningLanguage')
    
    if (savedNativeLanguage && savedLearningLanguage) {
      setFormData(prev => ({
        ...prev,
        nativeLanguage: savedNativeLanguage,
        learningLanguage: savedLearningLanguage
      }))
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(formData.email, formData.password, formData.nativeLanguage, formData.learningLanguage)
      
      // Save language preferences for next time
      localStorage.setItem('nativeLanguage', formData.nativeLanguage)
      localStorage.setItem('learningLanguage', formData.learningLanguage)
      
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="page-content">
      <div className="auth-container">
        <h1>Login</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Your Native Language</label>
            <select
              name="nativeLanguage"
              value={formData.nativeLanguage}
              onChange={handleChange}
              required
            >
              <option value="">Select your native language</option>
              {LANGUAGES.map(lang => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Language You Want to Learn</label>
            <select
              name="learningLanguage"
              value={formData.learningLanguage}
              onChange={handleChange}
              required
            >
              <option value="">Select language to learn</option>
              {LANGUAGES.filter(lang => lang !== formData.nativeLanguage).map(lang => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          <button type="submit" disabled={loading} className="auth-submit">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="auth-link">
          Don't have an account? <Link to="/signup">Sign up here</Link>
        </p>
      </div>
    </div>
  )
}

export default Login