import React, { useState, useContext } from 'react'
import axiosInstance from '../axiosInstance'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faSpinner } from '@fortawesome/free-solid-svg-icons'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../AuthProvider'

const Register = () => {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setIsLoggedIn, setUser } = useContext(AuthContext)

  const handleRegistration = async (e) => {
    e.preventDefault()
    setLoading(true)
    setSuccess(false)
    setErrors({})

    const userData = {
      username,
      email,
      password,
    }

    try {
      await axiosInstance.post('/register/', userData)
      const loginResponse = await axiosInstance.post('/token/', { username, password })
      localStorage.setItem('accessToken', loginResponse.data.access)
      localStorage.setItem('refreshToken', loginResponse.data.refresh)
      const profileResponse = await axiosInstance.get('/protected-view/')
      setUser(profileResponse.data.user ?? { username, email })
      setIsLoggedIn(true)
      navigate('/dashboard')
    } catch (error) {
      setErrors(error.response?.data || { non_field_errors: 'Registration failed. Please check your details.' })
      console.error('Registration error: ', error.response?.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='container'>
      <div className='row justify-content-center'>
        <div className='col-md-6 auth-panel glass-card p-5'>
          <div className='auth-heading text-center'>
            <span className='eyebrow'>Ready to start</span>
            <h3 className='text-light mb-4'>Create an Account</h3>
            <p className='lead'>Sign up and launch your next stock forecast with data-driven insights.</p>
          </div>

          <form onSubmit={handleRegistration}>
            <div className='mb-3'>
              <input type='text' className='form-control' placeholder='Username' value={username} onChange={(e) => setUsername(e.target.value)} />
              {errors.username && <div className='text-danger mt-2'>{errors.username}</div>}
            </div>

            <div className='mb-3'>
              <input type='email' className='form-control' placeholder='Email address' value={email} onChange={(e) => setEmail(e.target.value)} />
              {errors.email && <div className='text-danger mt-2'>{errors.email}</div>}
            </div>

            <div className='mb-3'>
              <input type='password' className='form-control' placeholder='Password' value={password} onChange={(e) => setPassword(e.target.value)} />
              {errors.password && <div className='text-danger mt-2'>{errors.password}</div>}
            </div>

            {success && <div className='alert alert-success'>Registration successful. You may log in now.</div>}

            {loading ? (
              <button type='submit' className='btn btn-info d-block mx-auto' disabled>
                <FontAwesomeIcon icon={faSpinner} spin /> Please wait...
              </button>
            ) : (
              <button type='submit' className='btn btn-info d-block mx-auto'>Register</button>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}

export default Register