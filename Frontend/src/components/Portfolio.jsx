import { Outlet, NavLink } from "react-router-dom"
import {useState, useEffect} from  'react'
import style from "./Style/Portfolio.module.css"
import "@fortawesome/fontawesome-free/css/all.min.css";




function Portfolio() {

    const [showBrokers, setShowBrokers] = useState(false);
    

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")   // call FastAPI backend
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error:", err));
  }, []);

    const brokers = ["Zerodha", "Upstox", "Groww", "Angelone"];




    return (
        <>


            {showBrokers && (
                <div className={style.overlay}>
                    <div className={style.brokerModal}>
                        <h3>Select a Broker</h3>
                        <ul>
                            {brokers.map((broker, index) => (
                                <li key={index}>{broker}</li>
                            ))}
                        </ul>
                        <button onClick={() => setShowBrokers(false)} className={style.closeBtn}>
                            Close
                        </button>
                    </div>
                </div>
            )}
            <div className={style.connectBroker}>
                
                <p>Connect to broker</p>
                <button
                    className={style.connectButton}
                    onClick={() => setShowBrokers(true)}
                >
                    <i className="fa-solid fa-plus"></i>
                </button>
            </div>


            <nav>

                <div><NavLink className={style.link} to="Stock">Stocks</NavLink></div>|
                <div><NavLink className={style.link} to="Mf">Mfs</NavLink></div>
                {/* <div><NavLink className={style.link} to="Other">Others</NavLink></div> */}

            </nav>
            <Outlet />

        </>
    )
}
export default Portfolio