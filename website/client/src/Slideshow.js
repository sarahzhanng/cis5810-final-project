import { Button } from "react-bootstrap";
import { useState, useContext, useEffect } from "react";
import { AuthContext } from "./AuthContext";
import { Heart, HeartFill } from "react-bootstrap-icons";

const Slideshow = ({ images = [], trigger }) => {
  const [index, setIndex] = useState(0);
  const { username } = useContext(AuthContext);
  const [savedImages, setSavedImages] = useState([]);

  const fetchSavedImages = () => {
    if (!username) return;
    fetch(`http://127.0.0.1:5000/get_saved_cloth/${username}`)
      .then((res) => res.json())
      .then((json) => {
        setSavedImages([...(json.static || []), ...(json.uploaded || [])]);
      })
      .catch(console.log);
  };

  useEffect(() => {
    fetchSavedImages();
  }, [username]);

  if (!images || images.length === 0) return null;

  const nextSlide = () => setIndex((prev) => (prev + 1) % images.length);
  const prevSlide = () => setIndex((prev) => (prev - 1 + images.length) % images.length);

  const currentImage = images[index];

  const toggleFavorite = (img) => {
    if (!username) return;

    const isSaved = savedImages.includes(img);
    const endpoint = isSaved ? "remove_cloth" : "save_cloth";
    const method = isSaved ? "DELETE" : "POST";

    fetch(`http://127.0.0.1:5000/${endpoint}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, cloth: img, uploaded: "F" }),
    })
      .then((res) => res.json())
      .then(() => {
        fetchSavedImages()
        trigger()
      })
      .catch(console.log);
  };

  return (
    <div
      style={{
        position: "relative",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        height: "100%",
        borderRadius: "12px",
        overflow: "hidden",
        backgroundColor: "#fff",
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
      }}
    >
      <img
        src={currentImage}
        alt={`Slide ${index + 1}`}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
        }}
      />

      {/* Previous Button */}
      <Button
        onClick={prevSlide}
        style={{
          position: "absolute",
          top: "50%",
          left: "10px",
          transform: "translateY(-50%)",
          width: "40px",
          height: "40px",
          borderRadius: "50%",
          backgroundColor: "rgba(0,0,0,0.5)",
          border: "none",
          color: "#fff",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: 0,
          fontWeight: "bold",
        }}
      >
        &lt;
      </Button>

      {/* Next Button */}
      <Button
        onClick={nextSlide}
        style={{
          position: "absolute",
          top: "50%",
          right: "10px",
          transform: "translateY(-50%)",
          width: "40px",
          height: "40px",
          borderRadius: "50%",
          backgroundColor: "rgba(0,0,0,0.5)",
          border: "none",
          color: "#fff",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: 0,
          fontWeight: "bold",
        }}
      >
        &gt;
      </Button>

      {/* Favorite Button */}
      {username && (
        <Button
          onClick={() => toggleFavorite(currentImage)}
          style={{
            position: "absolute",
            top: "10px",
            right: "10px",
            width: "36px",
            height: "36px",
            borderRadius: "50%",
            backgroundColor: savedImages.includes(currentImage) ? "red" : "rgba(0,0,0,0.3)",
            border: "none",
            color: "#fff",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            padding: 0,
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.backgroundColor = savedImages.includes(currentImage) ? "darkred" : "rgba(0,0,0,0.6)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.backgroundColor = savedImages.includes(currentImage) ? "red" : "rgba(0,0,0,0.3)")
          }
        >
          {savedImages.includes(currentImage) ? <HeartFill size={18} /> : <Heart size={18} />}
        </Button>
      )}

      {/* Slide Indicators */}
      <div
        style={{
          position: "absolute",
          bottom: "10px",
          width: "100%",
          display: "flex",
          justifyContent: "center",
          gap: "6px",
        }}
      >
        {images.map((_, i) => (
          <div
            key={i}
            style={{
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              backgroundColor: i === index ? "#4CAF50" : "#ccc",
              transition: "background-color 0.3s",
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default Slideshow;
