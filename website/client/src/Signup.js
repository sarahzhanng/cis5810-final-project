import { Button, TextField } from "@mui/material"
import { useState } from "react";


const Signup = () => {

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [response, setResponse] = useState(null)

  const handleSignUp = () => {
    if (username.length == 0 || password.length == 0) {
      setResponse('Username and password cannot be empty')
    } else {
      fetch(`http://127.0.0.1:5000/sign_up`, {
        method: 'POST',
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
        setResponse(json['message'])
      }).catch(err => {
        console.log(err)
        setResponse('Internal server error.')
      })
    }
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
      <h1>Sign Up</h1>
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
          onClick={handleSignUp}
        >
          Sign Up
        </Button>
        {response && <p>{response}</p>}
      </div>
    </div>
    </div>
  )
}

export default Signup