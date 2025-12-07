import React, { useState, useEffect, useContext } from "react";
import { AuthContext } from "./AuthContext";
import { X } from "react-bootstrap-icons";

const Capture = ({ numCols = 3 }) => {
  const { username } = useContext(AuthContext);
  const [captures, setCaptures] = useState([]);

  // Fetch saved captures for the current user
  const fetchCaptures = () => {
    if (!username) return;
    fetch(`http://127.0.0.1:5000/get_saved_capture/${username}`)
      .then((res) => res.json())
      .then((data) => setCaptures(data.result || []))
      .catch(console.error);
  };

  useEffect(() => {
    fetchCaptures();
  }, [username]);

  const deleteCapture = (img) => {
    if (!username) return;
    fetch(`http://127.0.0.1:5000/remove_capture`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, 'img': img }),
    })
      .then(() => {
        fetchCaptures();
        // if (trigger) trigger();
      })
      .catch(console.error);
  };

  const colStyle = {
    width: `${100 / numCols}%`,
    padding: "8px",
    boxSizing: "border-box",
  };

  return (
    <div style={{ display: "flex", flexWrap: "wrap", margin: "-8px" }}>
      {captures.map((img) => (
        <div key={img} style={colStyle}>
          <div
            style={{
              position: "relative",
              overflow: "hidden",
              borderRadius: "10px",
              boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
              cursor: "pointer",
              backgroundColor: "#fff",
              transition: "transform 0.2s",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.03)")}
            onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
          >
            <img
              src={img}
              alt="capture"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                display: "block",
              }}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteCapture(img);
              }}
              style={{
                position: "absolute",
                top: "6px",
                right: "6px",
                width: "32px",
                height: "32px",
                backgroundColor: "rgba(255,0,0,0.8)",
                border: "none",
                borderRadius: "6px",
                color: "#fff",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                cursor: "pointer",
                padding: 0,
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = "rgba(255,0,0,1)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = "rgba(255,0,0,0.8)")
              }
            >
              <X size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Capture;
