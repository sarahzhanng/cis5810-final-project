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

  const [tab, setTab] = useState('general')
  

return (
    <div className="container">

        <div className="d-flex mb-3" style={{ gap: "12px" }}>
            <button
                className={`btn ${tab === 'general' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setTab("general")}
            >
                General
            </button>

            <button
                className={`btn ${tab === 'favorites' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setTab("favorites")}
                disabled={savedImages.length === 0}  // optional
            >
                Favorites
            </button>
        </div>

            {(() => {
                if (tab === "general") return (

                )
                // if (tab === "favorites") return renderGrid(itemData.filter(i => savedImages.includes(i.img)));
            })()}
    </div>
)
}


export default Cloth;
