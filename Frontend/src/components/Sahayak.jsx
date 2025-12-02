import { useState, useEffect, useRef } from "react";
import { Outlet, NavLink } from "react-router-dom";
import style from "./Style/Sahayak.module.css";

export default function Sahayak() {
    const [symbol, setSymbol] = useState("");
    const [finalSymbol, setFinalSymbol] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const [fullList, setFullList] = useState([]);   // ✅ FIXED
    const [searchList, setSearchList] = useState([]);
    const [showList, setShowList] = useState(false);

    const [highlightIndex, setHighlightIndex] = useState(-1);
    const inputRef = useRef(null);

    // 📌 Load JSON from public folder
    useEffect(() => {
        fetch("/stock-list/nse_stock_details.json")
            .then((res) => res.json())
            .then((data) => setFullList(data))     // ✅ FIXED
            .catch((err) => console.error("JSON Load Error:", err));
    }, []);

    // Bold highlight function
    const highlightMatch = (text, query) => {
        const idx = text.toLowerCase().indexOf(query.toLowerCase());
        if (idx === -1) return text;

        return (
            <>
                {text.substring(0, idx)}
                <b>{text.substring(idx, idx + query.length)}</b>
                {text.substring(idx + query.length)}
            </>
        );
    };

    // 🔍 Search logic
    const handleSearch = (value) => {
        setSymbol(value);
        setHighlightIndex(-1);

        if (!value.trim()) {
            setSearchList([]);
            setShowList(false);
            return;
        }

        const filtered = fullList.filter(     // ✅ FIXED (was stockList)
            (item) =>
                item.symbol.toLowerCase().startsWith(value.toLowerCase()) ||
                item.name?.toLowerCase().includes(value.toLowerCase())
        );

        setSearchList(filtered.slice(0, 5));
        setShowList(true);
    };

    // ⌨ Keyboard navigation
    const handleKeyDown = (e) => {
        if (!showList || searchList.length === 0) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlightIndex((prev) =>
                prev < searchList.length - 1 ? prev + 1 : 0
            );
        } 
        else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlightIndex((prev) =>
                prev > 0 ? prev - 1 : searchList.length - 1
            );
        } 
        else if (e.key === "Enter") {
            if (highlightIndex !== -1) {
                const selected = searchList[highlightIndex].symbol;
                setSymbol(selected);
                setShowList(false);
            }
        }
    };

    const handleSubmit = () => {
        if (!symbol.trim()) {
            setError("Please enter a stock symbol.");
            return;
        }

        setError("");

        const cleaned = symbol.trim().toUpperCase();
        const final = cleaned.endsWith(".NS") ? cleaned : `${cleaned}.NS`;

        setLoading(true);
        setFinalSymbol(final);
        setShowList(false);
    };

    return (
        <div className={style.sahayakWrapper}>

            {/* Input Section */}
            <div className={style.inputBlock}>
                <input
                    ref={inputRef}
                    type="text"
                    placeholder="Enter Stock (e.g., TCS, RELIANCE)"
                    value={symbol}
                    onChange={(e) => handleSearch(e.target.value)}
                    onKeyDown={handleKeyDown}
                />

                <button onClick={handleSubmit} disabled={loading}>
                    {loading ? "Loading..." : "OK"}
                </button>

                {loading && <span className={style.loader}></span>}
                {error && <p className={style.errorText}>{error}</p>}

                {/* 🔽 Autocomplete Dropdown */}
                {showList && searchList.length > 0 && (
                    <div className={style.searchDropdown}>
                        {searchList.map((item, idx) => (
                            <div
                                key={idx}
                                className={`${style.searchItem} ${
                                    highlightIndex === idx
                                        ? style.highlightItem
                                        : ""
                                }`}
                                onClick={() => {
                                    setSymbol(item.symbol);
                                    setShowList(false);
                                }}
                            >
                                <div className={style.symbolBig}>
                                    {highlightMatch(item.symbol, symbol)}
                                </div>

                                <div className={style.subInfo}>
                                    {highlightMatch(item.name || "Unknown", symbol)} —{" "}
                                    {item.industry || "NA"}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Nav Tabs */}
            <nav className={style.navBar}>
                <NavLink
                    to="Fundamental"
                    className={({ isActive }) =>
                        isActive ? style.activeLink : style.link
                    }
                >
                    Fundamental
                </NavLink>

                <span className={style.divider}>|</span>

                <NavLink
                    to="Analysis"
                    className={({ isActive }) =>
                        isActive ? style.activeLink : style.link
                    }
                >
                    Analysis
                </NavLink>
            </nav>

            {/* Pass final symbol */}
            <Outlet context={{ symbol: finalSymbol, setLoading }} />
        </div>
    );
}
