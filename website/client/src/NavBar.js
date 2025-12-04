import { useContext, useEffect, useState } from "react"
import { AuthContext } from "./AuthContext"
import { ToastContainer, toast, Bounce } from 'react-toastify';

const NavBar = () => {

    const { username, setUsername } = useContext(AuthContext)

    const logout = () => {
        fetch(`http://127.0.0.1:5000/logout`, {
            credentials: 'include'
        })
        .then(res => res.json())
        .then(json => {
            console.log(json)
            setUsername(null)
toast.info('Logout successful', {
position: "bottom-center",
autoClose: 4000,
hideProgressBar: true,
closeOnClick: true,
pauseOnHover: true,
draggable: false,
progress: undefined,
theme: "light",
transition: Bounce,
});
        })
        .catch(err => {
            console.log(err)
        })
    }

    return (
        <div style={{
            width: "100%",
            backgroundColor: "darkgreen",
            padding: "10px 20px",
            boxSizing: "border-box"
        }}>
<ToastContainer
position="bottom-center"
autoClose={4000}
hideProgressBar={true}
newestOnTop={false}
closeOnClick={true}
rtl={false}
pauseOnFocusLoss={false}
draggable={false}
pauseOnHover
theme="light"
transition={Bounce}
/>

            <ul style={{
                listStyle: "none",
                display: "flex",
                margin: 0,
                padding: 0,
                gap: "20px", // space between items
            }}>
                <li>
                    <a 
                        href="/tryon"
                        style={{
                            color: "white",
                            textDecoration: "none",
                            fontWeight: "bold",
                            padding: "8px 12px",
                            borderRadius: "4px",
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = "green"}
                        onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
                    >
                        Try On
                    </a>
                </li>
                <li>
                    <a 
                        href="/suggestion"
                        style={{
                            color: "white",
                            textDecoration: "none",
                            fontWeight: "bold",
                            padding: "8px 12px",
                            borderRadius: "4px",
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = "green"}
                        onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
                    >
                        Suggestion
                    </a>
                </li>
                
                {username ? <>
                    <li>
                        <span 
                            style={{
                                color: "white",
                                textDecoration: "none",
                                fontWeight: "bold",
                                padding: "8px 12px",
                                borderRadius: "4px",
                                cursor: 'pointer'
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = "green"}
                            onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
                            onClick={logout}
                        >
                            Logout
                        </span>
                    </li>

                    <li>
                        <span 
                            style={{
                                color: "white",
                                textDecoration: "none",
                                fontWeight: "bold",
                                padding: "8px 12px",
                                borderRadius: "4px",
                            }}
                        >
                        {username}
                        </span>
                    </li>
                </>
                :
                <>
                    <li>
                        <a 
                            href="/login"
                            style={{
                                color: "white",
                                textDecoration: "none",
                                fontWeight: "bold",
                                padding: "8px 12px",
                                borderRadius: "4px",
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = "green"}
                            onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
                        >
                            Login
                        </a>
                    </li>

                    <li>
                        <a 
                            href="/signup"
                            style={{
                                color: "white",
                                textDecoration: "none",
                                fontWeight: "bold",
                                padding: "8px 12px",
                                borderRadius: "4px",
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = "green"}
                            onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
                        >
                            Signup
                        </a>
                    </li>
                    
                </>}
            </ul>
        </div>
    )
}

export default NavBar