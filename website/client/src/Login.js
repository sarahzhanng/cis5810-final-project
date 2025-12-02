
import { Button, TextField } from "@mui/material"
import { useState } from "react";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [response, setResponse] = useState(null)

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
      console.log(res)
      return res.json()
    }).then(json => {
      console.log(json)
      setResponse(json['message'])
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
        onChange={(e) => setUsername(e.target.value)}
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
        {response && <p>{response}</p>}
      </div>
    </div>
    </div>
  )
}

export default Login