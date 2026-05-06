import { useContext, useEffect, useState } from 'react'
import Button from './Button'
import { Link, useNavigate } from 'react-router-dom'
import { AuthContext } from '../AuthProvider'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRightFromBracket, faMoon, faSun } from '@fortawesome/free-solid-svg-icons'

const Header = () => {
  const { isLoggedIn, setIsLoggedIn, user } = useContext(AuthContext)
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')
  const [toastMessage, setToastMessage] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const applyTheme = () => {
      document.body.classList.remove('theme-light', 'theme-dark')
      document.body.classList.add(theme === 'light' ? 'theme-light' : 'theme-dark')
      localStorage.setItem('theme', theme)
      setToastMessage(`Switched to ${theme === 'dark' ? 'dark' : 'light'} mode`)
    }

    applyTheme()
  }, [theme])

  useEffect(() => {
    if (!toastMessage) return
    const timer = setTimeout(() => setToastMessage(''), 2200)
    return () => clearTimeout(timer)
  }, [toastMessage])

  const handleLogout = () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    setIsLoggedIn(false)
    navigate('/login')
  }

  const toggleTheme = () => {
    setTheme((current) => (current === 'dark' ? 'light' : 'dark'))
  }

  return (
    <header className='container'>
      <nav className='navbar'>
        <Link className='navbar-brand' to='/'>
          <span className='brand-mark'>SP</span>
          <span>Stock Prediction Portal</span>
        </Link>

        <div className='app-actions'>
          {user && (
            <span className='header-welcome'>Hi, {user.username}</span>
          )}
          <button className='btn btn-outline-info theme-btn' onClick={toggleTheme}>
            <FontAwesomeIcon icon={theme === 'dark' ? faSun : faMoon} />
            {theme === 'dark' ? 'Light' : 'Dark'} mode
          </button>
          {isLoggedIn ? (
            <>
              <Button text='Dashboard' class='btn-info' url='/dashboard' />
              <Button text='Profile' class='btn-outline-info' url='/profile' />
              <button className='btn btn-danger' onClick={handleLogout}>
                <FontAwesomeIcon icon={faArrowRightFromBracket} /> Logout
              </button>
            </>
          ) : (
            <>
              <Button text='Login' class='btn-outline-info' url='/login' />
              <Button text='Register' class='btn-info' url='/register' />
            </>
          )}
        </div>
      </nav>
      {toastMessage && <div className='theme-toast'>{toastMessage}</div>}
    </header>
  )
}

export default Header