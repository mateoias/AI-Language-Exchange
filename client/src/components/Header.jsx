import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Header({ onToggleSidebar }) {
  const { user, logout } = useAuth()

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {user && (
          <button 
            onClick={onToggleSidebar}
            className="sidebar-toggle"
          >
            ☰
          </button>
        )}
        <h1>Language Exchange</h1>
      </div>
      
      <div className="header-right">
        {user ? (
          <>
            <span className="user-info">
              Hi, {user.username} — Learning: {user.learningLanguage}
            </span>
            <Link to="/personalization" className="header-link">Settings</Link>
            <button onClick={logout} className="logout-btn">Logout</button>
          </>
        ) : (
          <nav>
            <Link to="/" className="header-link">Home</Link>
            <Link to="/about" className="header-link">About</Link>
            <Link to="/login" className="header-link">Login</Link>
          </nav>
        )}
      </div>
    </header>
  )
}

export default Header