import ImageUpload from "./ImageUpload";
import { HeartFill, Heart } from 'react-bootstrap-icons';
import React, { useContext, useEffect, useState } from "react";
import { AuthContext } from "./AuthContext";

const Cloth = ({ itemData, num_cols, handleSelection, upload, trigger }) => {
  const { username } = useContext(AuthContext);
  const [selected, setSelected] = useState(null);
  const [savedImages, setSavedImages] = useState({ uploaded: [], static: [] });

  const fetchSavedImg = () => {
    if (!username) return;
    fetch(`http://127.0.0.1:5000/get_saved_cloth/${username}`)
      .then(res => res.json())
      .then(json => setSavedImages(json))
      .catch(console.log);
  };

  useEffect(() => fetchSavedImg(), [username]);

  const selectImage = (img) => {
    setSelected(img.startsWith('blob') ? 'uploaded' : img);
    handleSelection(img);
  };

  const handleSave = (img) => {
    const isSaved = savedImages.static.includes(img) || savedImages.uploaded.includes(img);
    const endpoint = isSaved ? 'remove_cloth' : 'save_cloth';
    const method = isSaved ? 'DELETE' : 'POST';

    if (img.startsWith('blob')) {
      fetch(img).then(r => r.blob()).then(blob => {
        const reader = new FileReader();
        reader.onloadend = () => {
          fetch(`http://127.0.0.1:5000/${endpoint}`, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, cloth: reader.result, uploaded: 'T' }),
          }).then(() => { fetchSavedImg(); trigger(); });
        };
        reader.readAsDataURL(blob);
      });
    } else {
      fetch(`http://127.0.0.1:5000/${endpoint}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, cloth: img, uploaded: 'F' }),
      }).then(() => { fetchSavedImg(); trigger(); });
    }
  };

  const colClass = `col-${Math.floor(12 / num_cols)} mb-3`;

  return (
    <div className="container-fluid">
      <div className="row gx-2 gy-2">
        {upload && (
          <div className={colClass}>
            <div
              className={`card text-center ${selected === 'uploaded' ? 'border-primary' : ''}`}
              style={{
                cursor: 'pointer',
                aspectRatio: '1 / 1',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '12px',
                backgroundColor: '#fff',
                borderRadius: '8px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                transition: 'transform 0.2s',
              }}
              onClick={() => setSelected('uploaded')}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.03)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              <ImageUpload handleUpload={(img) => { selectImage(img); handleSave(img); }} />
            </div>
          </div>
        )}

        {itemData?.map(item => (
          <div className={colClass} key={item}>
            <div
              className={`card position-relative ${selected === item ? 'border-primary' : ''}`}
              style={{
                cursor: 'pointer',
                aspectRatio: '1 / 1',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                overflow: 'hidden',
                backgroundColor: '#fff',
                borderRadius: '8px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                transition: 'transform 0.2s, border 0.2s',
                border: selected === item ? '2px solid #4CAF50' : '1px solid #ddd',
              }}
              onClick={() => selectImage(item)}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.03)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              <img
                src={item}
                alt="cloth"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
              {username && (
                <button
                  onClick={e => { e.stopPropagation(); handleSave(item); }}
                  style={{
                    position: 'absolute',
                    top: '6px',
                    right: '6px',
                    width: '32px',
                    height: '32px',
                    backgroundColor: savedImages.static.includes(item) || savedImages.uploaded.includes(item) ? 'red' : 'rgba(0,0,0,0.3)',
                    border: 'none',
                    borderRadius: '6px',
                    color: '#fff',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = savedImages.static.includes(item) || savedImages.uploaded.includes(item) ? 'darkred' : 'rgba(0,0,0,0.6)'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = savedImages.static.includes(item) || savedImages.uploaded.includes(item) ? 'red' : 'rgba(0,0,0,0.3)'}
                >
                  {savedImages.static.includes(item) || savedImages.uploaded.includes(item) ? <HeartFill size={16} /> : <Heart size={16} />}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Cloth;
