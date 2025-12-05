import { useContext } from "react";
import { AuthContext } from "./AuthContext";
import { ToastContainer, toast, Bounce } from "react-toastify";

export default function NavBar() {
  const { username, setUsername } = useContext(AuthContext);

  const logout = () => {
    fetch(`http://127.0.0.1:5000/logout`, { credentials: "include" })
      .then((res) => res.json())
      .then((json) => {
        console.log(json);
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
      <nav className="navbar navbar-expand-lg navbar-dark px-3 shadow-sm"
        style={{
          backgroundColor: 'darkgreen'
        }}
      >
        {/* <a className="navbar-brand fw-bold" href="/">App</a> */}
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <a className="nav-link" href="/tryon">Try-On</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/suggestion">Suggestions</a>
            </li>
          </ul>

          <ul className="navbar-nav ms-auto">
            {username ? (
              <>
                <li className="nav-item">
                  <button className="btn btn-outline-light me-2" onClick={logout}>Logout</button>
                </li>
                <li className="nav-item d-flex align-items-center text-white fw-bold">{username}</li>
              </>
            ) : (
              <>
                <li className="nav-item">
                  <a className="btn btn-outline-light me-2" href="/login">Login</a>
                </li>
                <li className="nav-item">
                  <a className="btn btn-outline-light" href="/signup">Sign Up</a>
                </li>
              </>
            )}
          </ul>
        </div>
      </nav>
    </>
  );
}