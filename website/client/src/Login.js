import { Button, TextField } from "@mui/material";
import { useContext, useState } from "react";
import { AuthContext } from "./AuthContext";
import { ToastContainer, toast, Bounce } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const Login = () => {
  const [username, setUsernameState] = useState("");
  const [password, setPassword] = useState("");

  const { setUsername } = useContext(AuthContext);

  const handleLogin = () => {
    fetch(`http://127.0.0.1:5000/login`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    })
      .then((res) => res.json())
      .then((json) => {
        toast.info(json["message"], {
          position: "bottom-center",
          autoClose: 4000,
          hideProgressBar: true,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: false,
          theme: "light",
          transition: Bounce,
        });
        setUsername(json["token"]);
      })
      .catch((err) => console.log(err));
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        backgroundColor: "#f9f9f9",
      }}
    >
      <ToastContainer
        position="bottom-center"
        autoClose={4000}
        hideProgressBar
        closeOnClick
        pauseOnHover
        draggable={false}
        theme="light"
        transition={Bounce}
      />

      <div
        style={{
          backgroundColor: "#fff",
          padding: "32px",
          borderRadius: "12px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          width: "100%",
          maxWidth: "400px",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        <h2 style={{ textAlign: "center", color: "#006400" }}>Login</h2>

        <TextField
          label="Username"
          variant="outlined"
          value={username}
          onChange={(e) => setUsernameState(e.target.value)}
          fullWidth
        />

        <TextField
          label="Password"
          type="password"
          variant="outlined"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          fullWidth
        />

        <Button
          onClick={handleLogin}
          style={{
            backgroundColor: "#4CAF50",
            color: "#fff",
            padding: "10px 0",
            borderRadius: "8px",
            fontWeight: "bold",
            textTransform: "none",
          }}
          fullWidth
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#45a049")}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#4CAF50")}
        >
          Login
        </Button>
      </div>
    </div>
  );
};

export default Login;
