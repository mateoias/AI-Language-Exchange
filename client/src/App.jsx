import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Chat from './pages/Chat'
import About from './pages/About'
import FAQs from './pages/FAQs'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Personalization from './pages/Personalization'
import Beginner from './pages/Beginner'
import Intermediate from './pages/Intermediate'
import Advanced from './pages/Advanced'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/faqs" element={<FAQs />} />
            <Route path="/beginner" element={<Beginner />} />
            <Route path="/intermediate" element={<Intermediate />} />
            <Route path="/advanced" element={<Advanced />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route 
              path="/chat" 
              element={
                <ProtectedRoute>
                  <Chat />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/personalization" 
              element={
                <ProtectedRoute>
                  <Personalization />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App