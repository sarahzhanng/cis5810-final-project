import React from "react";
import Webcam from "react-webcam";

const Live = ({ webcamRef, image }) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <div
        style={{
          flex: 1,
          position: "relative",
        //   borderRadius: "8px",
          overflow: "hidden",
          backgroundColor: "#000",
        }}
      >
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          mirrored={true}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
        />

        {image && (
          <img
            src={image}
            alt="Captured"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "contain",
            }}
          />
        )}
      </div>
    </div>
  );
};

export default Live;
