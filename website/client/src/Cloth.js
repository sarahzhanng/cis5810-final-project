import React, { useContext, useEffect, useState } from "react";
import { AuthContext } from "./AuthContext";
import ImageUpload from "./ImageUpload";
import { HeartFill, Heart } from 'react-bootstrap-icons';

const Cloth = ({ itemData, num_cols, handleSelection, upload }) => {
  const { username } = useContext(AuthContext);
  const [selected, setSelected] = useState(null);
  const [savedImages, setSavedImages] = useState([]);

  const fetchSavedImg = () => {
    if (username) {
      fetch(`http://127.0.0.1:5000/get_saved_cloth/${username}`)
        .then(res => res.json())
        .then(json => setSavedImages(json['result']))
        .catch(err => console.log(err));
    }
  };

  useEffect(() => {
    fetchSavedImg();
  }, [username]);

  const selectImage = (img) => {
    setSelected(img);
    handleSelection(img);
  };

  const handleSave = (e, img) => {
    e.stopPropagation();
    const endpoint = savedImages.includes(img) ? 'remove_cloth' : 'save_cloth';
    const method = savedImages.includes(img) ? 'DELETE' : 'POST';

    fetch(`http://127.0.0.1:5000/${endpoint}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, cloth: img })
    })
      .then(res => res.json())
      .then(() => fetchSavedImg())
      .catch(err => console.log(err));
  };

  const colClass = `col-${Math.floor(12 / num_cols)} mb-4`;

  return (
    <div className="container">
      <div className="row gx-3 gy-3">
        {upload &&
          <div className={colClass}>
            <div
              className={`card text-center ${selected === "uploaded" ? "border-primary" : ""}`}
              style={{
                cursor: "pointer",
                padding: "12px",
                aspectRatio: '1 / 1', // makes it square
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onClick={() => setSelected('uploaded')}
            >
              <ImageUpload handleUpload={(img) => selectImage(img)} />
            </div>
          </div>
        }

        {itemData.map((item) => (
          <div className={colClass} key={item.img}>
            <div
              className={`card position-relative ${selected === item.img ? "border-primary" : ""}`}
              style={{
                cursor: "pointer",
                overflow: 'hidden',
                aspectRatio: '1 / 1', // square
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onClick={() => selectImage(item.img)}
            >
              <img
                src={item.img}
                className="card-img-top"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                }}
                alt="cloth"
              />
              {username &&
                <button
                  onClick={(e) => handleSave(e, item.img)}
                  className="btn position-absolute"
                  style={{
                    top: "8px",
                    right: "8px",
                    width: '32px',
                    height: '32px',
                    backgroundColor: savedImages.includes(item.img) ? 'red' : 'rgba(0,0,0,0.3)',
                    borderRadius: "0%", // square
                    border: "none",
                    color: "white",
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = savedImages.includes(item.img) ? 'darkred' : 'rgba(0,0,0,0.6)'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = savedImages.includes(item.img) ? 'red' : 'rgba(0,0,0,0.3)'}
                >
                  {savedImages.includes(item.img) ? <HeartFill size={16} /> : <Heart size={16} />}
                </button>
              }
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Cloth;
