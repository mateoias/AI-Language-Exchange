import { Link } from 'react-router-dom'

function Sidebar({ isOpen }) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-section">
        <h3>Learning Levels</h3>
        <ul>
          <li><Link to="/beginner">Beginner</Link></li>
          <li><Link to="/intermediate">Intermediate</Link></li>
          <li><Link to="/advanced">Advanced</Link></li>
        </ul>
      </div>
      
      <div className="sidebar-section">
        <h3>Topics</h3>
        <ul>
          <li><Link to="/topics/greetings">Greetings</Link></li>
          <li><Link to="/topics/travel">Travel</Link></li>
          <li><Link to="/topics/business">Business</Link></li>
          <li><Link to="/topics/culture">Culture</Link></li>
        </ul>
      </div>
      
      <div className="sidebar-section">
        <h3>Resources</h3>
        <ul>
          <li><Link to="/readings">Readings</Link></li>
          <li><Link to="/exercises">Exercises</Link></li>
          <li><Link to="/progress">Progress</Link></li>
        </ul>
      </div>
    </aside>
  )
}

export default Sidebar