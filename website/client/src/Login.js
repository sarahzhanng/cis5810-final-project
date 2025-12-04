
import { Button, TextField } from "@mui/material"
import { useContext, useState } from "react";
import { AuthContext } from "./AuthContext";

import { ToastContainer, toast, Bounce } from 'react-toastify';

const Login = () => {
  const [username, setUsernameState] = useState("");
  const [password, setPassword] = useState("");
  const [response, setResponse] = useState(null)

  const { setUsername } = useContext(AuthContext)

  const handleLogin = () => {
    fetch(`http://127.0.0.1:5000/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "username": username,
        "password": password
      })
    }).then(res => {
      return res.json()
    }).then(json => {
toast.info(json['message'], {
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
      // setResponse()
      setUsername(json['token'])
    }).catch(err => {
      console.log(err)
    })
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "calc(100vh - 52px)",
      }}
    >
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
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "50vw",
        gap: "16px"
      }}
    >
      <h1>Login</h1>
      <TextField
        label="Username"
        value={username}
        onChange={(e) => setUsernameState(e.target.value)}
      />
      <TextField
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <div
        style={{
          display: 'flex',
          flexDirection: 'row'
        }}
      >
        <Button 
          onClick={handleLogin}
        >
          Login
        </Button>
      </div>
    </div>
    </div>
  )
}

export default Login