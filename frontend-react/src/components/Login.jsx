import React, { useContext, useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSpinner } from '@fortawesome/free-solid-svg-icons'
import axiosInstance from '../axiosInstance'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../AuthProvider'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const { setIsLoggedIn, setUser } = useContext(AuthContext)

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const userData = { username, password }

    try {
      const response = await axiosInstance.post('/token/', userData)
      localStorage.setItem('accessToken', response.data.access)
      localStorage.setItem('refreshToken', response.data.refresh)
      const profileResponse = await axiosInstance.get('/protected-view/')
      setUser(profileResponse.data.user ?? { username })
      setIsLoggedIn(true)
      navigate('/dashboard')
    } catch (error) {
      setError('Invalid credentials. Please try again.')
      console.error('Invalid credentials', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='container'>
      <div className='row justify-content-center'>
        <div className='col-md-6 auth-panel glass-card p-5'>
          <div className='auth-heading text-center'>
            <span className='eyebrow'>Welcome back</span>
            <h3 className='text-light mb-4'>Login to your Portal</h3>
            <p className='lead'>Sign in to access your stock projections, charts, and performance metrics.</p>
          </div>

          <form onSubmit={handleLogin}>
            <div className='mb-3'>
              <input type='text' className='form-control' placeholder='Username' value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div className='mb-3'>
              <input type='password' className='form-control' placeholder='Password' value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>

            {error && <div className='alert alert-error'>{error}</div>}

            {loading ? (
              <button type='submit' className='btn btn-info d-block mx-auto' disabled>
                <FontAwesomeIcon icon={faSpinner} spin /> Logging in...
              </button>
            ) : (
              <button type='submit' className='btn btn-info d-block mx-auto'>Login</button>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}

export default Login