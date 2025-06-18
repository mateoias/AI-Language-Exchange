import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'


function Header({ onToggleSidebar }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const formatLevel = (level) => {
    if (!level) return ''
    return level.charAt(0).toUpperCase() + level.slice(1)
  }

return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button 
          onClick={onToggleSidebar}
          className="sidebar-toggle"
        >
          ☰
        </button>
        <h1>Language Exchange</h1>
      </div>
      
      <div className="header-right">
        {user ? (
          <>
            <span className="user-info">
              Hi, {user.username} - {formatLevel(user.proficiencyLevel)} - {user.learningLanguage}
            </span>
            <Link to="/personalization" className="header-link">Settings</Link>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </>
        ) : (
          <nav>
            <Link to="/" className="header-link">Home</Link>
            <Link to="/about" className="header-link">About</Link>
            <Link to="/faqs" className="header-link">FAQs</Link>
            <Link to="/login" className="header-link">Login</Link>
          </nav>
        )}
      </div>
    </header>
  )
}
export default Header