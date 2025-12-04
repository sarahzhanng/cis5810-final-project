import Live from './Live.js'
import Cloth from './Cloth.js'
import { useState, useRef, useEffect } from 'react'

import { io } from "socket.io-client"
const socket = io('http://127.0.0.1:5000')


const topItems = [
  {img: 'https://m.media-amazon.com/images/I/81ZTK8LKN1L._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81l5ZD2Gg8L._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81x2mbPJiBL._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81jc1857thL._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/71cT-YOkpgL._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/61RqkqCmbEL._AC_SX425_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/71dmd0tYXFL._AC_SX425_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/71sXZvJbTTL._AC_SY550_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/611IUuDJqfL._AC_SY550_.jpg'},
  {img: 'http://pngimg.com/uploads/dress/dress_PNG156.png'}
]

const bottomItems = [
  {img: 'https://m.media-amazon.com/images/I/61aW0cb7yYL._AC_SX522_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/41GLfOLu95L._AC_SX679_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81AJRqjL2rL._AC_SX425_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/614y7WrU2qL._AC_SY550_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/51R4+9nBP+L._AC_SX425_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/7112VPq8vAL._AC_SY550_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/719-rbuKySL._AC_SY741_.jpg'}
]

const TryOn = () => {
  const webcamRef = useRef(null);
  const [testImg, setTestImg] = useState(null)
  const [tryonState, setTryonState] = useState(false)

  const [cloth, setCloth] = useState({
    'top': null,
    'bottom': null
  })

  const handleCloth = (id, img) => {
    setCloth(prev => ({
      ...prev,
      [id]: img
    }))
  }

  const clothRef = useRef(cloth)

  useEffect(() => {
    clothRef.current = cloth
  }, [cloth])

  useEffect(() => {
    socket.on('receive_update', (data) => {
      console.log("received")
      const blob = new Blob([data], {type: "image/png"})
      const url = URL.createObjectURL(blob)
      setTestImg(url)
    })
    
    socket.on('reminder', () => {
      console.log('remindered')
      tryonButton()
    })
  }, [])

  const tryonButton = () => {
    console.log('starting trying on')
    setTryonState(true)
    const screenshot = webcamRef.current.getScreenshot()
    
    fetch(clothRef.current['top'])
      .then(res => res.blob())
      .then(blob => blob.arrayBuffer())
      .then(buffer => {
        socket.emit('send_message', screenshot, buffer)
      }).catch(err => {
        console.log(err)
      })
    
  }

  const stopTryonButton = () => {
    setTryonState(false)
    socket.emit('stop_thread')
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row'
      }}
    >
      <div
        style={{
          height: '100%',
          width: '100%'
        }}
      >
        <Live webcamRef={webcamRef}/>
        {tryonState ? 
          <button onClick={stopTryonButton}>Stop Try-On</button>
        :
          <button onClick={tryonButton}>Start Try-On</button>
        }
        
      </div>
      <div
        style={{
          height: '100%',
          width: '100%'
        }}
      >
        <Cloth 
          id='top' 
          num_cols={2}
          itemData={topItems} 
          handleSelection={(img) => handleCloth('top', img)}
          upload={true}
        />        
      </div>
      <div
        style={{
          height: '100%',
          width: '100%'
        }}
      >
        <Cloth 
          id='bottom'
          num_cols={2}
          itemData={bottomItems}
          handleSelection={(img) => handleCloth('bottom', img)}
          upload={true}
        />
      </div>

      {testImg && 
        <img src={testImg}/>
      }
    </div>
  )
}

export default TryOn;
