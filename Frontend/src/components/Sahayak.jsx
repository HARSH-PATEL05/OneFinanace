import { useState } from "react";
import { Outlet, NavLink } from "react-router-dom";
import style from "./Style/Sahayak.module.css";

export default function Sahayak() {
  const [symbol, setSymbol] = useState("");
  const [finalSymbol, setFinalSymbol] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false); // 🔥 loading state

  const handleSubmit = () => {
    if (!symbol.trim()) {
      setError("Please enter a stock symbol.");
      return;
    }

    setError("");

    const cleaned = symbol.trim().toUpperCase();
    const final = cleaned.endsWith(".NS") ? cleaned : `${cleaned}.NS`;

    setLoading(true);      // 🔥 start loading
    setFinalSymbol(final);
  };

  // Disable nav until user has entered a symbol
  const isDisabled = !finalSymbol;

  return (
    <div className={style.sahayakWrapper}>
      
      {/* 🔹 Input Section */}
      <div className={style.inputBlock}>
        <input
          type="text"
          placeholder="Enter Stock (e.g., TCS, RELIANCE)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />

        <button onClick={handleSubmit} disabled={loading}>
          {loading ? "Loading..." : "OK"}
        </button>

        {/* 🔥 Loader beside OK button */}
        {loading && <span className={style.loader}></span>}

        {error && <p className={style.errorText}>{error}</p>}
      </div>

      {/* 🔹 Navigation Tabs */}
      <nav className={style.navBar}>
        <NavLink
          to="Fundamental"
          className={({ isActive }) =>
            isDisabled
              ? style.disabledLink       // ❌ Cannot click until stock entered
              : isActive
              ? style.activeLink          // 🔵 Active tab
              : style.link                // ⚪ Inactive tab
          }
          onClick={(e) => isDisabled && e.preventDefault()}
        >
          Fundamental
        </NavLink>

        <span className={style.divider}>|</span>

        <NavLink
          to="Analysis"
          className={({ isActive }) =>
            isDisabled
              ? style.disabledLink
              : isActive
              ? style.activeLink
              : style.link
          }
          onClick={(e) => isDisabled && e.preventDefault()}
        >
          Analysis
        </NavLink>
      </nav>

      {/* 🔹 Children receive symbol + loading controller */}
      <Outlet context={{ symbol: finalSymbol, setLoading }} />
    </div>
  );
}
