import Live from './Live.js';
import Cloth from './Cloth.js';
import { useState, useRef, useEffect, useContext } from 'react';
import { AuthContext } from "./AuthContext";
import { io } from "socket.io-client";

const socket = io('http://127.0.0.1:5000', { autoConnect: true });

const TryOn = () => {
  const webcamRef = useRef(null);
  const [testImg, setTestImg] = useState(null);
  const [tryonState, setTryonState] = useState(false);
  const [cloth, setCloth] = useState({ top: null, bottom: null });
  const clothRef = useRef(cloth);

  const [view, setView] = useState('all');
  const [topItems, setTopItems] = useState([]);
  const [bottomItems, setBottomItems] = useState([]);

  const { username } = useContext(AuthContext);
  const [savedImages, setSavedImages] = useState([]);

  const fetchSavedImg = () => {
    if (!username) return;

    fetch(`http://127.0.0.1:5000/get_saved_cloth/${username}`)
      .then(res => res.json())
      .then(json => {
        const combined = [...(json.static || []), ...(json.uploaded || [])];
        setSavedImages(combined);
      })
      .catch(console.log);
  };

  useEffect(() => {
    fetchSavedImg();
  }, [username]);

  useEffect(() => {
    clothRef.current = cloth;
  }, [cloth]);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch(`https://virtual-tryon-backend-974u.onrender.com/transparent/list`);
        let json = await res.json();
        json = json.filter(item => !item.startsWith('.'));
        
        const result = [];

        while (result.length < 9 && json.length > 0) {
          const randomIndex = Math.floor(Math.random() * json.length);
          const selected = `https://virtual-tryon-backend-974u.onrender.com/transparent_static/${json[randomIndex]}`;
          console.log(json[randomIndex])
          try {
            const r = await fetch(selected);
            const blob = await r.blob();
            if (blob.type.startsWith("image/")) {
              result.push(selected);
            }
          } catch {}

          json.splice(randomIndex, 1);
        }

        setTopItems(result);
      } catch (e) {
        console.log(e);
      }
    };

    run();
  }, []);

  const tryonStateRef = useRef(false);

useEffect(() => {
  tryonStateRef.current = tryonState;
}, [tryonState]);

useEffect(() => {
  const handleUpdate = (data) => {
    const blob = new Blob([data], { type: "image/png" });
    const url = URL.createObjectURL(blob);
    setTestImg(url);
  };

  const handleReminder = () => {
    if (tryonStateRef.current) {
      tryonButton();
    }
  };

  socket.on('receive_update', handleUpdate);
  socket.on('reminder', handleReminder);

  return () => {
    socket.off('receive_update', handleUpdate);
    socket.off('reminder', handleReminder);
  };
}, []);


  const handleCloth = (id, img) => {
    setCloth((prev) => ({ ...prev, [id]: img }));
  };

  const tryonButton = () => {
    if (!webcamRef.current) return;

    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) return;

    setTryonState(true);
    tryonStateRef.current = true

    if (clothRef.current.top) {
      fetch(clothRef.current.top)
        .then(res => res.blob())
        .then(blob => blob.arrayBuffer())
        .then(buffer => socket.emit('send_message', screenshot, buffer))
        .catch(console.log);
    }
  };

  const stopTryonButton = () => {
  setTryonState(false);
  tryonStateRef.current = false;
  setTestImg(null);
  socket.emit('stop_thread');
};


return (
  <div
    style={{
      display: 'flex',
      height: 'calc(100vh - 2rem)',
      padding: '12px',
      gap: '16px',
      backgroundColor: '#f7f7f7',      // light app background
    }}
  >

    {/* LEFT — Live cam */}
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#ffffff',
        borderRadius: '10px',
        padding: '12px',
        boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
      }}
    >
      <div style={{ flex: 1, display: "flex" }}>
        <Live webcamRef={webcamRef} image={testImg} style={{ flex: 1, borderRadius: "6px" }} />
      </div>

      {/* Buttons */}
      {tryonState ? (
        <button
          onClick={stopTryonButton}
          style={{
            marginTop: '12px',
            backgroundColor: '#d9534f',
            color: '#fff',
            padding: '10px 16px',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Stop Try-On
        </button>
      ) : (
        <button
          onClick={tryonButton}
          style={{
            marginTop: '12px',
            backgroundColor: '#4CAF50',
            color: '#fff',
            padding: '10px 16px',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Start Try-On
        </button>
      )}
    </div>


    {/* RIGHT — Clothes */}
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        overflowY: 'auto',
        backgroundColor: '#ffffff',
        borderRadius: '10px',
        padding: '16px',
        boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
      }}
    >
      {/* Toggle buttons */}
      <div>
        <button
          onClick={() => setView("all")}
          style={{
            marginRight: '10px',
            backgroundColor: view === 'all' ? '#006400' : '#ffffff',
            color: view === 'all' ? '#fff' : '#006400',
            padding: '8px 14px',
            border: '1px solid #006400',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Clothes
        </button>

        <button
          onClick={() => setView("favorites")}
          style={{
            backgroundColor: view === 'favorites' ? '#006400' : '#ffffff',
            color: view === 'favorites' ? '#fff' : '#006400',
            padding: '8px 14px',
            border: '1px solid #006400',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Favorites
        </button>
      </div>

      {/* Clothing list */}
      {view === "all" ? (
        <Cloth
          id="top"
          num_cols={4}
          itemData={topItems}
          handleSelection={(img) => handleCloth("top", img)}
          upload={true}
          trigger={() => fetchSavedImg()}
        />
      ) : savedImages.length > 0 && (
        <Cloth
          id="top"
          num_cols={4}
          itemData={savedImages}
          handleSelection={(img) => handleCloth("top", img)}
          upload={false}
          trigger={() => fetchSavedImg()}
        />
      )}
    </div>
  </div>
);
};

export default TryOn;
