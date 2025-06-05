import { useState } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'
import { useAuth } from '../context/AuthContext'

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user } = useAuth()

  return (
    <div className="app-layout">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
      {user && <Sidebar isOpen={sidebarOpen} />}
      <main className={`main-content ${user && sidebarOpen ? '' : 'no-sidebar'}`}>
        {children}
      </main>
    </div>
  )
}

export default Layout