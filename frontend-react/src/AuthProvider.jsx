import { useState, useContext, createContext } from 'react'

// Create the context
const AuthContext = createContext();

const AuthProvider = ({children}) => {
    const [isLoggedIn, setIsLoggedIn] = useState(
        !!localStorage.getItem('accessToken')
    )
  return (
    <AuthContext.Provider value={{isLoggedIn, setIsLoggedIn}}>
        {children}
        {/* basically the children means all the app components   */}
    </AuthContext.Provider>
  )
}

export default AuthProvider
export {AuthContext};