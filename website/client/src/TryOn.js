import Live from './Live.js';
import Cloth from './Cloth.js';
import { useState, useRef, useEffect } from 'react';
import { io } from "socket.io-client";
const socket = io('http://127.0.0.1:5000');

const topItems = [
  'https://m.media-amazon.com/images/I/81ZTK8LKN1L._AC_UL480_FMwebp_QL65_.jpg',
 'https://m.media-amazon.com/images/I/81l5ZD2Gg8L._AC_UL480_FMwebp_QL65_.jpg',
  // 'https://m.media-amazon.com/images/I/81x2mbPJiBL._AC_UL480_FMwebp_QL65_.jpg',
  'https://m.media-amazon.com/images/I/81x2mbPJiBL._AC_UL480_FMwebp_QL65_.jpg',
  'https://m.media-amazon.com/images/I/81jc1857thL._AC_UL480_FMwebp_QL65_.jpg',
  'https://m.media-amazon.com/images/I/71cT-YOkpgL._AC_UL480_FMwebp_QL65_.jpg',
  'https://m.media-amazon.com/images/I/61RqkqCmbEL._AC_SX425_.jpg',
  'https://m.media-amazon.com/images/I/71dmd0tYXFL._AC_SX425_.jpg',
  'https://m.media-amazon.com/images/I/71sXZvJbTTL._AC_SY550_.jpg',
  'https://m.media-amazon.com/images/I/611IUuDJqfL._AC_SY550_.jpg',
];

const bottomItems = [
  'https://m.media-amazon.com/images/I/61aW0cb7yYL._AC_SX522_.jpg',
  'https://m.media-amazon.com/images/I/41GLfOLu95L._AC_SX679_.jpg',
  'https://m.media-amazon.com/images/I/81AJRqjL2rL._AC_SX425_.jpg',
  'https://m.media-amazon.com/images/I/614y7WrU2qL._AC_SY550_.jpg',
  'https://m.media-amazon.com/images/I/51R4+9nBP+L._AC_SX425_.jpg',
  'https://m.media-amazon.com/images/I/7112VPq8vAL._AC_SY550_.jpg',
  'https://m.media-amazon.com/images/I/719-rbuKySL._AC_SY741_.jpg'
];

const TryOn = () => {
  const webcamRef = useRef(null);
  const [testImg, setTestImg] = useState(null);
  const [tryonState, setTryonState] = useState(false);
  const [cloth, setCloth] = useState({ top: null, bottom: null });
  const clothRef = useRef(cloth);

  useEffect(() => { clothRef.current = cloth }, [cloth]);

  useEffect(() => {
    socket.on('receive_update', (data) => {
      const blob = new Blob([data], { type: "image/png" });
      const url = URL.createObjectURL(blob);
      setTestImg(url);
    });

    socket.on('reminder', () => tryonButton());
  }, []);

  const handleCloth = (id, img) => {
    setCloth(prev => ({ ...prev, [id]: img }));
  };

  const tryonButton = () => {
    setTryonState(true);
    const screenshot = webcamRef.current.getScreenshot();
    if (clothRef.current['top']) {
      fetch(clothRef.current['top'])
      .then(res => res.blob())
      .then(blob => blob.arrayBuffer())
      .then(buffer => socket.emit('send_message', screenshot, buffer))
      .catch(console.log);
    } else if (clothRef.current['bottom']) {
      fetch(clothRef.current['bottom'])
      .then(res => res.blob())
      .then(blob => blob.arrayBuffer())
      .then(buffer => socket.emit('send_message', screenshot, buffer))
      .catch(console.log);
    }
    
  };

  const stopTryonButton = () => {
    setTryonState(false);
    setTestImg(null)
    socket.emit('stop_thread');
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 2rem)', gap: '8px', padding: '8px' }}>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Live webcamRef={webcamRef} image={testImg} style={{ flex: 1 }} />
        {tryonState ? 
          <button onClick={stopTryonButton}>Stop Try-On</button> :
          <button onClick={tryonButton}>Start Try-On</button>
        }
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Cloth
          id='top'
          num_cols={4}
          itemData={topItems}
          handleSelection={(img) => handleCloth('top', img)}
          upload={true}
        />
      </div>

      {/* <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Cloth
          id='bottom'
          num_cols={2}
          itemData={bottomItems}
          handleSelection={(img) => handleCloth('bottom', img)}
          upload={true}
        />
      </div> */}
    </div>
  );
};

export default TryOn;
