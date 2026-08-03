import { useState, useEffect } from "react";
import style from './Style/Stock.module.css';
import StocksCard from './Card';
import {
    fetchAllPortfolios,
    fetchLiveHoldingsLTP,
    fetchDailyStockSnapshot,
    fetchMarketStatus,
    fetchFilteredStocks
} from "@/Api";

function Stock() {
    const [allHoldings, setAllHoldings] = useState({});
    const [ltpMap, setLtpMap] = useState({});
    const [loading, setLoading] = useState(false);
    const [marketStatus, setMarketStatus] = useState("unknown");
    const [brokerColors, setBrokerColors] = useState({});
    const [indicator, setIndicator] = useState("rsi");
    const [condition, setCondition] = useState(null);
    const [customRange, setCustomRange] = useState({ min: "", max: "" });
    const [filteredStocks, setFilteredStocks] = useState([]);
    const runDailySnapshotIfNeeded = async () => {
        const today = new Date().toDateString();
        const lastRun = localStorage.getItem("daily_snapshot_stock");

        if (lastRun !== today) {
            await fetchDailyStockSnapshot();
            localStorage.setItem("daily_snapshot_stock", today);
        }
    };

    const scheduleDailySnapshot = () => {
        const now = new Date();
        const target = new Date();
        target.setHours(9, 0, 0, 0);

        if (now > target) target.setDate(target.getDate() + 1);

        const msUntilRun = target - now;

        setTimeout(async () => {
            await fetchDailyStockSnapshot();
            localStorage.setItem("daily_snapshot_stock", new Date().toDateString());
            scheduleDailySnapshot();
        }, msUntilRun);
    };

    const loadPortfolios = async () => {
        setLoading(true);
        try {
            // 1️⃣ Load instantly from cache if available
            const cached = localStorage.getItem("Stock_portfolio_cache");
            if (cached) {
                setAllHoldings(JSON.parse(cached));
            }


            const data = await fetchAllPortfolios();
            setAllHoldings(data);
            // extract unique broker names
            const brokers = Object.keys(data);


            // assign colors
            const colors = {};
            brokers.forEach((b, i) => {
                colors[b] = predefinedColors[i % predefinedColors.length];
            });
            setBrokerColors(colors);


            // 3️⃣ Save to cache for instant stock view next time
            localStorage.setItem("Stock_portfolio_cache", JSON.stringify(data));

            const map = {};
            Object.values(data).forEach(brokerData => {
                brokerData.holdings.forEach(stock => {
                    map[stock.symbol] = stock.Ltp;
                });
            });

            setLtpMap(map);

        } catch (err) {
            console.error("Error fetching holdings:", err);
        } finally {
            setLoading(false);
        }
    };

    // ===== LIVE LTP =====
    const loadLiveLTP = async () => {
        const ltpData = await fetchLiveHoldingsLTP();
        console.log("🔥 Fetched live LTP:", ltpData);   // DEBUG

        setLtpMap(prev => {
            const updated = { ...prev };
            ltpData.forEach(item => {
                updated[item.symbol] = item.Ltp;
            });
            console.log("🎯 New LTP Map:", updated);      // DEBUG
            return updated;
        });


    };
    const predefinedColors = [
        "#e57373", "#64b5f6", "#81c784", "#ba68c8",
        "#ffb74d", "#4db6ac", "#9575cd", "#90a4ae"
    ];

    // Run daily snapshot + initial portfolio load
    useEffect(() => {
        runDailySnapshotIfNeeded();
        scheduleDailySnapshot();
        loadPortfolios();
    }, []);

    // =========== NEW MARKET-DRIVEN POLLING LOGIC ===========
    useEffect(() => {
        let timerId;

        const controlPolling = async () => {
            let status;

            try {
                status = await fetchMarketStatus();   // { status, nextCheckSeconds }
            } catch (e) {
                console.error("Market status fetch error:", e);
                timerId = setTimeout(controlPolling, 60000);
                return;
            }

            setMarketStatus(status.state);
            console.log("🕒 Market:", status);
            console.log("🕒 Marketstatus", marketStatus);
            if (status.open) {
                await loadLiveLTP();     // only fetch LTP when market open
                timerId = setTimeout(controlPolling, 1000);  // 1 sec refresh
            } else {
                console.log("⏸ Market closed, next check:", status.nextCheckSeconds);
                timerId = setTimeout(controlPolling, status.nextCheckSeconds * 1000);
            }
        };

        controlPolling();
        return () => clearTimeout(timerId);

    }, []);

    // ===== CALCULATIONS (unchanged) =====
    let totalInvested = 0;
    let currentValue = 0;
    let dayPL = 0;

    Object.values(allHoldings).forEach(brokerData => {
        brokerData.holdings.forEach(stock => {
            const qty = stock.Qty;
            const avgPrice = stock.average_price;
            const ltp = ltpMap[stock.symbol] !== undefined ? ltpMap[stock.symbol] : stock.Ltp;
            const prev_ltp = stock.prev_ltp;

            totalInvested += avgPrice * qty;
            currentValue += ltp * qty;
            dayPL += (ltp - prev_ltp) * qty;
        });
    });

    const overallPL = currentValue - totalInvested;
    const overallPLPercent = totalInvested > 0 ? (overallPL / totalInvested) * 100 : 0;
    const dayPLPercent = currentValue > 0 ? (dayPL / currentValue) * 100 : 0;

    const currentValueColor =
        currentValue > totalInvested ? style.green :
            currentValue < totalInvested ? style.red : "";

    const overallPLColor =
        overallPL > 0 ? style.green :
            overallPL < 0 ? style.red : "";

    const overallPLPercentColor =
        overallPLPercent > 0 ? style.green :
            overallPLPercent < 0 ? style.red : "";

    const dayPLColor =
        dayPL > 0 ? style.green :
            dayPL < 0 ? style.red : "";

    const dayPLPercentColor =
        dayPLPercent > 0 ? style.green :
            dayPLPercent < 0 ? style.red : "";

    const fmt = (num) => {
        if (num > 0) return `+${num.toFixed(2)}`;
        if (num < 0) return `-${Math.abs(num).toFixed(2)}`;
        return "0.00";
    };

    const fmtPercent = (num) => {
        if (num > 0) return `+${num.toFixed(2)}%`;
        if (num < 0) return `-${Math.abs(num).toFixed(2)}%`;
        return "0.00%";
    };
    const indicatorOptions = {
        rsi: [
            { label: "Oversold (<30) (Bounce Expected)", type: "<", value: 30 },
            { label: "Weak (30-50)", type: "between", min: 30, max: 50 },
            { label: "Strong (50-70)", type: "between", min: 50, max: 70 },
            { label: "Overbought (>70) (Possible Fall)", type: ">", value: 70 }
        ],
        volume: [
            { label: "High Demand (>2x Avg)", type: ">", value: 2 },
            { label: "Normal Volume", type: "between", min: 0.5, max: 2 }
        ],
        macd: [
            { label: "Bullish (MACD > Signal)", type: ">", value: 0 },
            { label: "Bearish (MACD < Signal)", type: "<", value: 0 }
        ],
        ma: [
            { label: "Above 50DMA (Bullish)", type: ">", value: "ma50" },
            { label: "Above 200DMA (Strong Trend)", type: ">", value: "ma200" }
        ]
    };
    const applyFilter = () => {
        const allStocksFlat = Object.entries(allHoldings)
            .flatMap(([brokerName, brokerData]) =>
                brokerData.holdings.map((stock) => ({
                    ...stock,
                    broker: brokerName
                }))
            );

        const result = allStocksFlat.filter((stock) => {
            let val;

            if (indicator === "rsi") val = stock.rsi ?? 50;
            if (indicator === "price") val = ltpMap[stock.symbol] ?? stock.Ltp;
            if (indicator === "volume") val = stock.volume ?? 1;
            if (indicator === "macd") val = stock.macd ?? 0;

            if (!condition) return false;

            if (condition.type === "<") return val < condition.value;
            if (condition.type === ">") return val > condition.value;

            if (condition.type === "between") {
                const min = customRange.min || condition.min;
                const max = customRange.max || condition.max;
                return val >= min && val <= max;
            }

            return false;
        });

        setFilteredStocks(result);
    };
    return (
        <div className={style.main}>
            <div className={style.Allstock}>
                <h2>OVERALL INVESTMENT</h2>
                <div className={style.grid}>
                    <div className={style.Dashboard}>
                        <h3>Total Invested</h3>
                        <h4>{totalInvested.toFixed(2)}</h4>
                    </div>

                    <div className={style.Dashboard}>
                        <h3>Current Value</h3>
                        <h4 className={currentValueColor}>{currentValue.toFixed(2)}</h4>
                    </div>

                    <div className={style.Dashboard}>
                        <h3>Overall P/L</h3>
                        <div className={style.flex}>
                            <h4 className={overallPLColor}>{fmt(overallPL)}</h4>
                            <h4 className={overallPLPercentColor}>{fmtPercent(overallPLPercent)}</h4>

                        </div>
                    </div>

                    <div className={style.Dashboard}>
                        <h3>Day P/L</h3>
                        <div className={style.flex}>
                            <h4 className={dayPLColor}>{fmt(dayPL)}</h4>
                            <h4 className={dayPLPercentColor}>{fmtPercent(dayPLPercent)}</h4>
                        </div>
                    </div>

                    <button
                        onClick={() => { loadPortfolios(); loadLiveLTP(); }}
                        disabled={loading}
                        className={style.RefreshButton}
                    >
                        {loading ? "REFRESHING..." : "REFRESH"}
                    </button>

                </div>
                <div className={style.FilterBox}>
                    <h3>📊 Smart Filter</h3>

                    {/* Indicator */}
                    <select
                        value={indicator}
                        onChange={(e) => {
                            setIndicator(e.target.value);
                            setCondition(null);
                        }}
                    >
                        <option value="rsi">RSI</option>
                        <option value="volume">Volume</option>
                        <option value="macd">MACD</option>
                        <option value="price">Price</option>
                    </select>

                    {/* Condition */}
                    <select
                        onChange={(e) => {
                            const index = e.target.value;
                            setCondition(indicatorOptions[indicator][index]);
                        }}
                    >
                        <option>Select Condition</option>
                        {indicatorOptions[indicator].map((opt, i) => (
                            <option key={i} value={i}>
                                {opt.label}
                            </option>
                        ))}
                    </select>

                    {/* BETWEEN INPUT */}
                    {condition?.type === "between" && (
                        <div className={style.rangeInputs}>
                            <input
                                type="number"
                                placeholder="Min"
                                value={customRange.min}
                                onChange={(e) =>
                                    setCustomRange({ ...customRange, min: e.target.value })
                                }
                            />
                            <input
                                type="number"
                                placeholder="Max"
                                value={customRange.max}
                                onChange={(e) =>
                                    setCustomRange({ ...customRange, max: e.target.value })
                                }
                            />
                        </div>
                    )}

                    <button onClick={applyFilter}>Apply</button>

                    {/* SUMMARY */}
                    {condition && (
                        <p className={style.summaryText}>{condition.label}</p>
                    )}

                    {/* RESULTS */}
                    <div className={style.filteredList}>
                        {filteredStocks.map((stock, index) => {
                            const ltp = ltpMap[stock.symbol] ?? stock.Ltp;

                            return (
                                <div key={index} className={style.filterCard}>
                                    <h4>{stock.symbol}</h4>
                                    <p>Price: ₹{ltp}</p>
                                    <p>Qty: {stock.Qty}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            <div className={style.Cards}>
                <ul className={style.List}>
                    {Object.entries(allHoldings)
                        .flatMap(([brokerName, brokerData]) =>
                            brokerData.holdings.map((stock) => ({ stock, broker: brokerName }))
                        )
                        .map((item, index) => (
                            <li key={index}>
                                <StocksCard
                                    symbol={item.broker}
                                    name={item.stock.name}
                                    Qty={item.stock.Qty}
                                    Avg={item.stock.average_price}
                                    Ltp={ltpMap[item.stock.symbol] !== undefined
                                        ? ltpMap[item.stock.symbol]
                                        : item.stock.Ltp
                                    }
                                    brokerColor={brokerColors[item.broker]}
                                />
                            </li>
                        ))}

                </ul>
            </div>
        </div>
    );
}

export default Stock;
