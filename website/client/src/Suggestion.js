import React, { useEffect, useState, useContext } from "react";
import { Button, Dropdown, DropdownButton } from "react-bootstrap";
import Cloth from "./Cloth";
import Slideshow from "./Slideshow";
import ImageUpload from "./ImageUpload";
import { AuthContext } from "./AuthContext";

const clothing_url = "https://virtual-tryon-backend-974u.onrender.com";

const Suggestion = () => {
  const [metadata, setMetadata] = useState([]);
  const [mode, setMode] = useState("tops");
  const [cloth, setCloth] = useState(null);
  const [result, setResult] = useState(null);

  const { username } = useContext(AuthContext);
  const [savedImages, setSavedImages] = useState([]);

  const fetchSavedImg = () => {
    if (username) {
      fetch(`http://127.0.0.1:5000/get_saved_cloth/${username}`)
        .then((res) => res.json())
        .then((json) => {
          setSavedImages((json.static || []).concat(json.uploaded || []));
        })
        .catch(console.log);
    }
  };

  useEffect(() => {
    fetchSavedImg();
  }, [username]);

  useEffect(() => {
    const run = async () => {
      if (mode !== "upload" && mode !== "favorite") {
        const res = await fetch(`${clothing_url}/${mode}`);
        let json = await res.json();
        json = json.map((item) => item.image_url);

        const result = [];
        while (result.length < 9 && json.length > 0) {
          const i = Math.floor(Math.random() * json.length);
          const url = clothing_url + json[i];

          try {
            const r = await fetch(url);
            const blob = await r.blob();
            if (blob.type.startsWith("image/")) result.push(url);
          } catch {}

          json.splice(i, 1);
        }
        setMetadata(result);
      } else if (mode === "favorite") {
        setMetadata(savedImages);
      } else {
        setMetadata(null);
      }
    };

    run();
  }, [mode]);

  const getSuggestion = () => {
    if (!cloth) return;

    const handlePhotoSuggestion = (fileBlob) => {
      const file = new File([fileBlob], "image.png", { type: "png" });
      const formData = new FormData();
      formData.append("file", file);
      fetch(`${clothing_url}/suggest_from_photo`, {
        method: "POST",
        body: formData,
      })
        .then((res) => res.json())
        .then((json) => setResult(json));
    };

    if (mode === "tops" || mode === "top") {
      fetch(`${clothing_url}/generate_looks_from_top`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ top_id: cloth }),
      })
        .then((res) => res.json())
        .then((json) => setResult(json));
    } else if (mode === "bottom" || mode === "bottoms") {
      fetch(`${clothing_url}/generate_looks_from_bottom`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bottom_id: cloth }),
      })
        .then((res) => res.json())
        .then((json) => setResult(json));
    } else if (mode === "upload" || mode === "favorite") {
      if (cloth.startsWith("http")) {
        fetch(cloth)
          .then((r) => r.blob())
          .then(handlePhotoSuggestion);
      } else {
        const type = cloth.split(";")[0].substring(5);
        const data = atob(cloth.split(",")[1]);
        const array = Uint8Array.from(data, (c) => c.charCodeAt(0));
        handlePhotoSuggestion(new Blob([array], { type }));
      }
    }
  };

  return (
    <div
      style={{
        height: "calc(100vh - 2rem)",
        padding: "16px",
        backgroundColor: "#f9f9f9",
      }}
    >
      <div
        style={{
          display: "flex",
          gap: "16px",
          height: "100%",
        }}
      >
        {/* LEFT PANEL */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            background: "#fff",
            borderRadius: "10px",
            padding: "16px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            overflow: "hidden",
          }}
        >
          <div style={{ marginBottom: "12px" }}>
            <DropdownButton title="Options" variant="light">
              <Dropdown.Item onClick={() => setMode("tops")}>Top</Dropdown.Item>
              <Dropdown.Item onClick={() => setMode("bottoms")}>
                Bottom
              </Dropdown.Item>
              <Dropdown.Item onClick={() => setMode("upload")}>
                Upload
              </Dropdown.Item>
              {username && 
              <Dropdown.Item onClick={() => setMode("favorite")}>
                Favorites
              </Dropdown.Item>
              }
            </DropdownButton>
          </div>

          <div
            style={{
              flex: 1,
              overflow: "auto",
              borderRadius: "8px",
            }}
          >
            {metadata ? (
              mode === "favorite" ? (
                <Cloth
                  itemData={metadata}
                  num_cols={3}
                  handleSelection={setCloth}
                  upload={false}
                  trigger={fetchSavedImg}
                />
              ) : mode === "upload" ? (
                <div
                  style={{
                    padding: "16px",
                    border: "2px dashed #ccc",
                    borderRadius: "10px",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "100%",
                    background: "#fafafa",
                  }}
                >
                  <ImageUpload handleUpload={(img) => setCloth(img)} />
                </div>
              ) : (
                <Cloth
                  itemData={metadata}
                  num_cols={3}
                  handleSelection={(img) =>
                    setCloth(
                      img.substring(
                        (clothing_url + "/static/").length,
                        img.length - 4
                      )
                    )
                  }
                  upload={false}
                />
              )
            ) : (
              <div
                style={{
                  height: "100%",
                  border: "2px dashed #ccc",
                  borderRadius: "10px",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  background: "#fafafa",
                }}
              >
                <ImageUpload handleUpload={(img) => setCloth(img)} />
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL — SUGGESTIONS */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            background: "#fff",
            borderRadius: "10px",
            padding: "16px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            overflow: "hidden",
          }}
        >
          <Button
            variant="success"
            onClick={getSuggestion}
            style={{
              width: "100%",
              marginBottom: "12px",
              padding: "10px",
              fontSize: "1rem",
            }}
          >
            Get Suggestion
          </Button>

          {result ? (
            <div
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
              }}
            >
              <div style={{ flex: 1, minHeight: 0 }}>
                <Slideshow
                  trigger={() => fetchSavedImg()}
                  images={result.looks.map((item) => {
                    if (item.top) return `${clothing_url}${item.top.image_url}`;
                    if (item.bottom)
                      return `${clothing_url}${item.bottom.image_url}`;
                    if (item.item)
                      return `${clothing_url}${item.item.image_url}`;
                    return null;
                  })}
                />
              </div>

              <div
                style={{
                  marginTop: "12px",
                  padding: "12px",
                  background: "#f7f7f7",
                  borderRadius: "8px",
                  maxHeight: "120px",
                  overflowY: "auto",
                  fontSize: "0.9rem",
                }}
              >
                <strong>Explanation:</strong> {result.explanation}
              </div>
            </div>
          ) : (
            <div
              style={{
                flex: 1,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                color: "#777",
                fontSize: "0.9rem",
              }}
            >
              No suggestions yet — choose an item!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Suggestion;
