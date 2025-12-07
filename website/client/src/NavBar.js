import { useContext } from "react";
import { AuthContext } from "./AuthContext";
import { ToastContainer, toast, Bounce } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function NavBar() {
  const { username, setUsername } = useContext(AuthContext);

  const logout = () => {
    fetch(`http://127.0.0.1:5000/logout`, { credentials: "include" })
      .then((res) => res.json())
      .then(() => {
        setUsername(null);
        toast.info("You have been logged out", {
          position: "bottom-center",
          autoClose: 4000,
          hideProgressBar: true,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: false,
          theme: "light",
          transition: Bounce,
        });
      })
      .catch((err) => console.log(err));
  };

  return (
    <>
      <ToastContainer position="bottom-center" autoClose={4000} hideProgressBar theme="light" transition={Bounce} />

      <nav
        className="navbar navbar-expand-lg px-4 shadow-sm"
        style={{
          backgroundColor: "#FFFFFF",
          fontFamily: "'Inter', 'Roboto', sans-serif",
          borderBottom: "1px solid #e5e5e5",
        }}
      >
        <button className="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarNav">
          {/* Left side links */}
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <a
                className="nav-link"
                href="/tryon"
                style={{
                  color: "#333",
                  fontWeight: 500,
                  transition: "color 0.2s",
                }}
                onMouseOver={(e) => (e.target.style.color = "#4CAF50")}
                onMouseOut={(e) => (e.target.style.color = "#333")}
              >
                Try-On
              </a>
            </li>

            <li className="nav-item">
              <a
                className="nav-link"
                href="/suggestion"
                style={{
                  color: "#333",
                  fontWeight: 500,
                  transition: "color 0.2s",
                }}
                onMouseOver={(e) => (e.target.style.color = "#4CAF50")}
                onMouseOut={(e) => (e.target.style.color = "#333")}
              >
                Suggestions
              </a>
            </li>
          </ul>

          {/* Right side login/user actions */}
          <ul className="navbar-nav ms-auto align-items-center">
            {username ? (
              <>
                <li className="nav-item me-2">
                  <a
                    className="btn"
                    href="/account"
                    style={{
                      borderRadius: "6px",
                      border: "1px solid #4CAF50",
                      color: "#4CAF50",
                      padding: "6px 16px",
                      transition: "all 0.2s",
                    }}
                    onMouseOver={(e) => {
                      e.target.style.backgroundColor = "#4CAF50";
                      e.target.style.color = "#fff";
                    }}
                    onMouseOut={(e) => {
                      e.target.style.backgroundColor = "#FFFFFF";
                      e.target.style.color = "#4CAF50";
                    }}
                  >
                    {username}
                  </a>
                </li>
                {/* <li
                  className="nav-item me-3"
                  style={{ color: "#333", fontWeight: "bold" }}
                >
                  {username}
                </li> */}

                <li className="nav-item">
                  <button
                    className="btn"
                    style={{
                      backgroundColor: "#4CAF50",
                      color: "#fff",
                      borderRadius: "6px",
                      padding: "6px 16px",
                      transition: "background-color 0.2s",
                    }}
                    onMouseOver={(e) => (e.target.style.backgroundColor = "#45a049")}
                    onMouseOut={(e) => (e.target.style.backgroundColor = "#4CAF50")}
                    onClick={logout}
                  >
                    Logout
                  </button>
                </li>
              </>
            ) : (
              <>
                <li className="nav-item me-2">
                  <a
                    className="btn"
                    href="/login"
                    style={{
                      borderRadius: "6px",
                      border: "1px solid #4CAF50",
                      color: "#4CAF50",
                      padding: "6px 16px",
                      transition: "all 0.2s",
                    }}
                    onMouseOver={(e) => {
                      e.target.style.backgroundColor = "#4CAF50";
                      e.target.style.color = "#fff";
                    }}
                    onMouseOut={(e) => {
                      e.target.style.backgroundColor = "#FFFFFF";
                      e.target.style.color = "#4CAF50";
                    }}
                  >
                    Login
                  </a>
                </li>

                <li className="nav-item">
                  <a
                    className="btn"
                    href="/signup"
                    style={{
                      borderRadius: "6px",
                      border: "1px solid #4CAF50",
                      color: "#4CAF50",
                      padding: "6px 16px",
                      transition: "all 0.2s",
                    }}
                    onMouseOver={(e) => {
                      e.target.style.backgroundColor = "#4CAF50";
                      e.target.style.color = "#fff";
                    }}
                    onMouseOut={(e) => {
                      e.target.style.backgroundColor = "#FFFFFF";
                      e.target.style.color = "#4CAF50";
                    }}
                  >
                    Sign Up
                  </a>
                </li>
              </>
            )}
          </ul>
        </div>
      </nav>
    </>
  );
}
