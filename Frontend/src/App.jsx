
import './App.css'
import { Route, Routes, NavLink } from 'react-router-dom'
import Portfolio from './components/Portfolio'
import Contact from './components/Contact'
import Sahayak from './components/Sahayak'
import Home from './components/Home'
import Error404 from './components/Error404'
import Stock from './components/portfolio/Stock'
import Mf from './components/portfolio/Mf'
import Other from './components/portfolio/Others'

function App() {
  return (

    <><div className='main'>
      <div className='logo'>
        <img src="/Images/OneFinance-logo.png" alt="no img" />

      </div>
      <div className='nav'>
        
          <div><NavLink  className="link " to="/">Accounts</NavLink></div> |
          <div> <NavLink className="link " to="/Sahayak">Sahayak</NavLink></div> |
          <div><NavLink  className="link " to="/Portfolio">Portfolio</NavLink></div>|
          <div><NavLink className="link" to="/Contact">Contact</NavLink></div>
        
      </div>
      <div className='login'>
        <button className='btn'>Login</button>
        <button className='btn'>Sign Up</button>
        <img src="/Images/download.jpg" alt="no img" className='user' />
      </div>
    </div>


      <Routes>
        <Route path="/components/" element={<Home />} />
        <Route index element={<Home />} />
        <Route path="/Sahayak" element={<Sahayak />} />
        <Route path="/Contact" element={<Contact />} />
        <Route path="/Portfolio" element={<Portfolio />} >
          <Route path='Stock' element={<Stock />} />
          <Route index element={<Stock />} />
          <Route path='Mf' element={<Mf />} />
          <Route path='Other' element={<Other />} />
        </Route>
        <Route path="*" element={<Error404 />} />

      </Routes>
    </>

  )
}

export default App
