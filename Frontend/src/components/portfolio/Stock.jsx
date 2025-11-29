import { useState, useEffect } from "react";
import style from './Style/Stock.module.css';
import StocksCard from './Card';
import {
    fetchAllPortfolios,
    fetchLiveHoldingsLTP,
    fetchDailyStockSnapshot,
    fetchMarketStatus       // <--- NEW
} from "@/Api";

function Stock() {
    const [allHoldings, setAllHoldings] = useState({});
    const [ltpMap, setLtpMap] = useState({});
    const [loading, setLoading] = useState(false);
    const [marketStatus, setMarketStatus] = useState("unknown");
    const [brokerColors, setBrokerColors] = useState({});

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
            const brokers = Object.keys(data);   // because your API returns { brokerName: {mfs:[]}}
            

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
    return (
        <div className={style.main}>
            <div className={style.Allstock}>
                <h2>Overall Investment</h2>
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
                        {loading ? "Refreshing..." : "Refresh"}
                    </button>

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
