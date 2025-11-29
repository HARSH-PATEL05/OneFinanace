import { Outlet, NavLink } from "react-router-dom";
import { useState, useEffect } from "react";
import style from "./Style/Portfolio.module.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import { fetchMarketStatus } from "@/Api";

function Portfolio() {
  const [showBrokers, setShowBrokers] = useState(false);
  const [showAngelForm, setShowAngelForm] = useState(false);

  const [marketStatus, setMarketStatus] = useState("Checking…");
  const [nextCheck, setNextCheck] = useState(60);
  const [holidayName, setHolidayName] = useState("");

  const [formData, setFormData] = useState({
    client_code: "",
    mpin: "",
    totp_secret: "",
  });

  const brokers = ["Zerodha", "Upstox", "Groww", "Angelone"];

  // =================== MARKET STATUS LOOP =====================
  useEffect(() => {
    let timerId;

    const loop = async () => {
      try {
        const res = await fetchMarketStatus();
        console.log("[Market Status]:", res);

        setMarketStatus(res.state);           // set backend state string
        setNextCheck(res.nextCheckSeconds);   // next check schedule
        setHolidayName(res.holidayName || "");

        timerId = setTimeout(loop, res.nextCheckSeconds * 1000);
      } catch (err) {
        console.error("Market Status Error:", err);
        timerId = setTimeout(loop, 60000); // fallback retry after 1 min
      }
    };

    loop();
    return () => clearTimeout(timerId);
  }, []);

  // =================== HELPERS =====================
  function formatCountdown(seconds) {
    if (seconds <= 0) return "Now";

    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);

    if (hrs > 0 && mins > 0) return `${hrs}h ${mins}m`;
    if (hrs > 0) return `${hrs}h`;
    return `${mins}m`;
  }

  function getMarketStatusDisplay(status, nextCheckSeconds, holidayName = "") {
    if (status === "Market Open") {
      return { text: "Market Open", subText: "Live", color: "green", icon: "🟢" };
    }

    if (status === "Opens at 09:15 AM") {
      return {
        text: "Before Market",
        subText: `Opens in ${formatCountdown(nextCheckSeconds)}`,
        color: "orange",
        icon: "🟡"
      };
    }

    if (status === "Closed for the day") {
      return {
        text: "Market Closed",
        subText: `Next in ${formatCountdown(nextCheckSeconds)}`,
        color: "gray",
        icon: "⚪"
      };
    }

    if (status === "Weekend") {
      return {
        text: "Weekend",
        subText: `Next in ${formatCountdown(nextCheckSeconds)}`,
        color: "gray",
        icon: "⚪"
      };
    }

    if (status.startsWith("Holiday")) {
      return {
        text: status,                 // Already includes "Holiday: XYZ"
        subText: `Next in ${formatCountdown(nextCheckSeconds)}`,
        color: "gray",
        icon: "⚪"
      };
    }

    return {
      text: "Checking…",
      subText: "",
      color: "gray",
      icon: "⏳"
    };
  }

  // Final UI object
  const display = getMarketStatusDisplay(marketStatus, nextCheck, holidayName);

  // =================== Broker Actions =====================
  const handleBrokerClick = (broker) => {
    const brokerName = broker.toLowerCase();
    if (brokerName === "angelone") {
      setShowAngelForm(true);
      setShowBrokers(false);
    } else {
      window.location.href = `http://127.0.0.1:8000/brokers/${brokerName}/login`;
    }
  };

  const handleAngelLogin = async (e) => {
    e.preventDefault();
    try {
      const formBody = new FormData();
      formBody.append("client_code", formData.client_code);
      formBody.append("mpin", formData.mpin);
      formBody.append("totp_secret", formData.totp_secret);

      const res = await fetch("http://127.0.0.1:8000/brokers/angelone/login", {
        method: "POST",
        body: formBody,
      });

      const data = await res.json();
      console.log("AngelOne login response:", data);

      if (data.status === "error") {
        alert(`Login failed: ${data.message}`);
      } else {
        alert("Login successful!");
        setShowAngelForm(false);
      }
    } catch (error) {
      console.error("Error logging in to AngelOne:", error);
      alert("Something went wrong during AngelOne login.");
    }
  };

  // =================== UI RETURN =====================
  return (
    <>
      {/* Overlay for Broker Selection */}
      {showBrokers && (
        <div className={style.overlay}>
          <div className={style.brokerModal}>
            <h3>Select a Broker</h3>
            <ul>
              {brokers.map((broker, index) => (
                <li key={index} onClick={() => handleBrokerClick(broker)}>
                  {broker}
                </li>
              ))}
            </ul>
            <button onClick={() => setShowBrokers(false)} className={style.closeBtn}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* AngelOne Login Form Modal */}
      {showAngelForm && (
        <div className={style.overlay}>
          <div className={style.brokerModal}>
            <h3>AngelOne Login</h3>
            <form onSubmit={handleAngelLogin}>
              <input
                type="text"
                placeholder="Client Code"
                value={formData.client_code}
                onChange={(e) => setFormData({ ...formData, client_code: e.target.value })}
                required
              />
              <input
                type="password"
                placeholder="MPIN"
                value={formData.mpin}
                onChange={(e) => setFormData({ ...formData, mpin: e.target.value })}
                required
              />
              <input
                type="text"
                placeholder="TOTP Secret"
                value={formData.totp_secret}
                onChange={(e) => setFormData({ ...formData, totp_secret: e.target.value })}
                required
              />

              <div style={{ marginTop: "10px" }}>
                <button type="submit" className={style.connectButton}>
                  Submit
                </button>
                <button
                  type="button"
                  onClick={() => setShowAngelForm(false)}
                  className={style.closeBtn}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Broker + Market Status */}
      <div className={style.connectBroker}>
        <div className={style.justify}>
          <p>Connect to broker</p>
          <button className={style.connectButton} onClick={() => setShowBrokers(true)}>
            <i className="fa-solid fa-plus"></i>
          </button>
        </div>
        <div className={style.justify}>
          <h3>{display.text}</h3>
          <button className={style.marketbutton}>{display.icon}</button>
        </div>
      </div>

      {/* Navigation */}
      <nav>
        <div>
          <NavLink className={style.link} to="Stock">
            Stocks
          </NavLink>
        </div>
        |
        <div>
          <NavLink className={style.link} to="Mf">
            Mfs
          </NavLink>
        </div>
      </nav>

      <Outlet />
    </>
  );
}

export default Portfolio;
