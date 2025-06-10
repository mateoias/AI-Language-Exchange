import { useState } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="app-layout">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
      <Sidebar isOpen={sidebarOpen} />
      <main className={`main-content ${sidebarOpen ? '' : 'no-sidebar'}`}>
        {children}
      </main>
    </div>
  )
}

export default Layout