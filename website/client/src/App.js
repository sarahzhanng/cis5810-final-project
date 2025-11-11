import { useState } from 'react';
import './App.css';
import Live from './Live.js'
import Cloth from './Cloth.js'

const topItems = [
  {img: 'https://m.media-amazon.com/images/I/81ZTK8LKN1L._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81l5ZD2Gg8L._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81x2mbPJiBL._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/81jc1857thL._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/71cT-YOkpgL._AC_UL480_FMwebp_QL65_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/61RqkqCmbEL._AC_SX425_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/71dmd0tYXFL._AC_SX425_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/71sXZvJbTTL._AC_SY550_.jpg'},
  {img: 'https://m.media-amazon.com/images/I/611IUuDJqfL._AC_SY550_.jpg'}
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

function App() {
  const [selectedImg, setSelectedImg] = useState({
    'top': '',
    'bottom': ''
  })

  const handleSelectionChange = (id, img) => {
    setSelectedImg((prev) => {
      return ({
        ...prev,
        [id]: img
      })
    })
  }

  return (
    <div className='app'>

      <div>
        <Live/>
        <Cloth 
          id='top' 
          itemData={topItems} 
          onSelectionChange={handleSelectionChange}
        />
        <Cloth 
          id='bottom'
          itemData={bottomItems}
          onSelectionChange={handleSelectionChange}
        />
      </div>
    </div>
  );
}

export default App;
