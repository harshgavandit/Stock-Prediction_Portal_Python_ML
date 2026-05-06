import { useState, useEffect, createContext } from 'react'
import axiosInstance from './axiosInstance'

// Create the context
const AuthContext = createContext();

const AuthProvider = ({children}) => {
    const [isLoggedIn, setIsLoggedIn] = useState(
        !!localStorage.getItem('accessToken')
    )
    const [user, setUser] = useState(null)

    useEffect(() => {
        const verifySession = async () => {
            if (!localStorage.getItem('accessToken')) {
                setIsLoggedIn(false)
                setUser(null)
                return
            }

            try {
                const response = await axiosInstance.get('/protected-view/')
                setIsLoggedIn(true)
                setUser(response.data.user ?? null)
            } catch {
                localStorage.removeItem('accessToken')
                localStorage.removeItem('refreshToken')
                setIsLoggedIn(false)
                setUser(null)
            }
        }

        verifySession()
    }, [])

    return (
      <AuthContext.Provider value={{isLoggedIn, setIsLoggedIn, user, setUser}}>
          {children}
      </AuthContext.Provider>
    )
}

export default AuthProvider
export {AuthContext};