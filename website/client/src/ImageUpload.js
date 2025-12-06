import { useRef, useState } from "react";

const ImageUpload = ({ handleUpload }) => {
  const inputRef = useRef(null);
  const [image, setImage] = useState(null);

  const handlePaste = async (event) => {
    const items = event.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.includes("image/")) {
        const blob = await item.getAsFile();
        const url = URL.createObjectURL(blob);
        setImage(url);
        handleUpload(url);
        break;
      }
    }
  };

  const handleInput = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setImage(url);
    handleUpload(url);
    event.target.value = "";
  };

  return (
    <div
      style={{
        height: "100%",
        width: "100%",
        boxSizing: "border-box",
        cursor: "pointer",
        border: "2px dashed #ccc",
        borderRadius: "8px",
        backgroundColor: "#fff",
        boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "border-color 0.2s, transform 0.2s",
      }}
      onPaste={handlePaste}
      onClick={() => inputRef.current.click()}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#4CAF50")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#ccc")}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleInput}
        style={{ display: "none" }}
      />

      {image ? (
        <div
          style={{
            position: "relative",
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <img
            src={image}
            alt="uploaded"
            style={{
              maxWidth: "100%",
              maxHeight: "100%",
              width: "100%",
              height: "100%",
              objectFit: "contain",
              display: "block",
            }}
          />
          <button
            onClick={(e) => {
              e.stopPropagation();
              setImage(null);
            }}
            style={{
              position: "absolute",
              top: 6,
              right: 6,
              background: "#4CAF50",
              color: "#fff",
              border: "none",
              borderRadius: "50%",
              width: 28,
              height: 28,
              cursor: "pointer",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "#45a049")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "#4CAF50")}
          >
            ×
          </button>
        </div>
      ) : (
        <p style={{ color: "#555", fontSize: "14px", textAlign: "center", padding: "10px" }}>
          Upload or paste an image
        </p>
      )}
    </div>
  );
};

export default ImageUpload;
