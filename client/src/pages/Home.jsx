import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'

function Home() {
  const { user } = useAuth()

  return (
    <div className="page-content">
      <h1>Welcome to Language Exchange AI</h1>
      
      {user ? (
        <div>
          <p>Hello {user.username}! Ready to practice {user.learningLanguage}?</p>
          <div style={{ marginTop: '2rem' }}>
            <Link to="/chat" className="cta-button">Start Chatting</Link>
          </div>
        </div>
      ) : (
        <div>
          <p>Your personal language learning companion.</p>
          <div style={{ marginTop: '2rem' }}>
            <h2>Get Started</h2>
            <p>Sign up to begin your language learning journey.</p>
            <div className="cta-buttons">
              <Link to="/signup" className="cta-button primary">Sign Up</Link>
              <Link to="/login" className="cta-button secondary">Login</Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Home