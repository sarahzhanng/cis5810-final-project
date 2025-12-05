import { Button } from "react-bootstrap";
import { useState } from "react";

const Slideshow = ({ images = [] }) => {
  const [index, setIndex] = useState(0);

  if (!images || images.length === 0) return null;

  const nextSlide = () => setIndex((prev) => (prev + 1) % images.length);
  const prevSlide = () => setIndex((prev) => (prev - 1 + images.length) % images.length);

  return (
    <div
      className="position-relative d-flex justify-content-center align-items-center border rounded overflow-hidden"
      style={{ height: "100%", width: "100%", backgroundColor: "#f8f9fa" }}
    >
      <img
        src={images[index]}
        alt={`Slide ${index + 1}`}
        style={{
          height: "100%",
          width: "100%",
          objectFit: "contain",
        }}
      />

      {/* Previous Button */}
      <Button
        variant="dark"
        onClick={prevSlide}
        className="position-absolute top-50 start-0 translate-middle-y"
        style={{
          width: "40px",
          height: "40px",
          opacity: 0.7,
          borderRadius: "50%",
          padding: 0,
        }}
      >
        &lt;
      </Button>

      {/* Next Button */}
      <Button
        variant="dark"
        onClick={nextSlide}
        className="position-absolute top-50 end-0 translate-middle-y"
        style={{
          width: "40px",
          height: "40px",
          opacity: 0.7,
          borderRadius: "50%",
          padding: 0,
        }}
      >
        &gt;
      </Button>

      {/* Slide Indicators
      <div className="position-absolute bottom-0 w-100 text-center mb-2">
        {images.map((_, i) => (
          <span
            key={i}
            className={`mx-1 rounded-circle ${i === index ? "bg-dark" : "bg-secondary"}`}
            style={{ display: "inline-block", width: "10px", height: "10px" }}
          />
        ))}
      </div> */}
    </div>
  );
};

export default Slideshow;
