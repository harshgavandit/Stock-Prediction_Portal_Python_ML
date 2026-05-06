import './assets/css/style.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AuthProvider from './AuthProvider'
import Header from './components/Header'
import Footer from './components/Footer'
import Main from './components/Main'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/dashboard/Dashboard'
import Profile from './components/Profile'
import PrivateRoute from './PrivateRoute'
import PublicRoute from './PublicRoute'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app-wrapper">
          <Header />

          <main className="flex-grow-1">
            <Routes>
              <Route path="/" element={<Main />} />
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <Login />
                  </PublicRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <PublicRoute>
                    <Register />
                  </PublicRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <PrivateRoute>
                    <Profile />
                  </PrivateRoute>
                }
              />
              <Route path="*" element={<Main />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
