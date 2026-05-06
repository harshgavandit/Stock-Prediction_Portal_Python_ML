import { useContext, useEffect, useState } from 'react'
import axiosInstance from '../axiosInstance'
import { AuthContext } from '../AuthProvider'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faUserCircle, faShieldAlt } from '@fortawesome/free-solid-svg-icons'

const Profile = () => {
  const { user, setUser } = useContext(AuthContext)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('')
  const [statusType, setStatusType] = useState('success')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setUsername(user.username || '')
      setEmail(user.email || '')
    }
  }, [user])

  useEffect(() => {
    if (!status) return
    const timer = setTimeout(() => setStatus(''), 4200)
    return () => clearTimeout(timer)
  }, [status])

  const getMessage = (error) => {
    if (!error) return 'Unable to update profile. Please try again.'
    if (typeof error === 'string') return error
    if (error.username) return error.username[0]
    if (error.email) return error.email[0]
    if (error.password) return error.password[0]
    return 'Unable to update profile. Please try again.'
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setStatus('')

    try {
      const payload = {
        username: username.trim(),
        email: email.trim(),
      }

      if (password.trim()) {
        payload.password = password.trim()
      }

      const response = await axiosInstance.patch('/profile/', payload)
      const latestUser = response.data.user || { username, email }
      setUser(latestUser)
      setStatusType('success')
      setStatus('Profile updated successfully.')
      setPassword('')
    } catch (error) {
      const message = error.response?.data || error.response?.data?.detail || error.message
      setStatusType('error')
      setStatus(getMessage(message))
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    return (
      <div className='container dashboard-panel'>
        <section className='dashboard-hero glass-card'>
          <h2>Loading profile...</h2>
          <p>Please wait while your account data is loaded.</p>
        </section>
      </div>
    )
  }

  return (
    <div className='container dashboard-panel'>
      <section className='dashboard-hero glass-card profile-panel'>
        <div className='hero-header'>
          <span className='eyebrow'>Account settings</span>
          <h2>Profile & security</h2>
          <p>Update your username, email, or password. Your account settings are saved securely to your profile.</p>
        </div>

        <div className='profile-intro'>
          <div className='profile-summary'>
            <FontAwesomeIcon icon={faUserCircle} />
            <div>
              <span>Signed in as</span>
              <strong>{user.email}</strong>
            </div>
          </div>
          <div className='profile-security'>
            <FontAwesomeIcon icon={faShieldAlt} />
            <div>
              <span>Security</span>
              <strong>Keep your password safe and update it regularly.</strong>
            </div>
          </div>
        </div>

        <form className='profile-form' onSubmit={handleSubmit}>
          <label>Username</label>
          <input
            type='text'
            className='form-control'
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder='Username'
            required
          />

          <label>Email</label>
          <input
            type='email'
            className='form-control'
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder='Email address'
            required
          />

          <label>New password</label>
          <input
            type='password'
            className='form-control'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder='Leave blank to keep current password'
          />

          <button type='submit' className='btn btn-primary' disabled={loading || !username.trim() || !email.trim()}>
            {loading ? 'Saving...' : 'Save changes'}
          </button>

          {status && (
            <div className={`alert ${statusType === 'success' ? 'alert-success' : 'alert-error'}`}>
              {status}
            </div>
          )}
        </form>
      </section>
    </div>
  )
}

export default Profile
