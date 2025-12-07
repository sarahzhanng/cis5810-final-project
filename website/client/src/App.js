import { useState } from 'react';
import './App.css';
import TryOn from './TryOn';
import NavBar from './NavBar';
import Suggestion from './Suggestion';
import Login from './Login';
import Signup from './Signup';
import { Route, Routes } from "react-router-dom";
import { AuthProvider } from './AuthContext';
import Capture from './Capture';

function App() {
  const [page, setPage] = useState('tryon')

  return (
    <AuthProvider>
      <NavBar/>

      <div>
        <Routes>
          <Route path="/" element={<TryOn />} />
          <Route path="/tryon" element={<TryOn />} />
          <Route path="/suggestion" element={<Suggestion />} />
          <Route path='/login' element={<Login /> } />
          <Route path='/signup' element={<Signup/> } />
          <Route path='/account' element={<Capture/>} />
        </Routes>
      </div>

    </AuthProvider>
  );
}

export default App;
