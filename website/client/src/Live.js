import React, { useState } from "react";
import Webcam from "react-webcam";

const Live = ({ webcamRef }) => {
  const [image, setImage] = useState(null);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%", // Fill parent panel vertically
        gap: "8px",
      }}
    >
      <div
        style={{
          flex: 1, // Webcam / captured image fills remaining space
          position: "relative",
          borderRadius: "8px",
          overflow: "hidden",
          backgroundColor: "#000",
        }}
      >
        {!image && (
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            mirrored={true}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        )}

        {image && (
          <img
            src={image}
            alt="Captured"
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              backgroundColor: "#000",
            }}
          />
        )}
      </div>

      <div style={{ display: "flex", gap: "8px" }}>
        {!image ? (
          <button
            style={{ flex: 1 }}
            onClick={() => setImage(webcamRef.current.getScreenshot())}
          >
            Capture Photo
          </button>
        ) : (
          <button style={{ flex: 1 }} onClick={() => setImage(null)}>
            Retake Photo
          </button>
        )}
      </div>
    </div>
  );
};

export default Live;
