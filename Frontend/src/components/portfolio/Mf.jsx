import { useState, useEffect } from "react";
import MFsCard from './Card';
import style from './Style/Stock.module.css';

import {
    fetchAllPortfolios,
    fetchDailyMfSnapshot
} from "@/Api";

function Mf() {
    const [allMFs, setAllMFs] = useState({});
    const [loading, setLoading] = useState(false);
    const [brokerColors, setBrokerColors] = useState({});


    /* ============================================================
       ⭐ DAILY SNAPSHOT (unchanged)
    ============================================================ */
    const runDailySnapshotIfNeeded = async () => {
        const today = new Date().toDateString();
        const lastRun = localStorage.getItem("daily_snapshot_mf");

        if (lastRun !== today) {
            await fetchDailyMfSnapshot();
            localStorage.setItem("daily_snapshot_mf", today);
        }
    };

    const scheduleDailySnapshot = () => {
        const now = new Date();
        const target = new Date();
        target.setHours(9, 0, 0, 0);

        if (now > target) target.setDate(target.getDate() + 1);

        const msUntilRun = target - now;

        setTimeout(async () => {
            await fetchDailyMfSnapshot();
            localStorage.setItem("daily_snapshot_mf", new Date().toDateString());
            scheduleDailySnapshot();
        }, msUntilRun);
    };

    /* ============================================================
       ⭐ HYBRID CACHE:
       1. Load MF instantly from frontend cache
       2. Fetch fresh from backend (Redis/DB) and update UI + cache
    ============================================================ */
    const loadData = async () => {
        setLoading(true);

        try {
            // 1️⃣ Load instantly from cache if available
            const cached = localStorage.getItem("mf_portfolio_cache");
            if (cached) {
                setAllMFs(JSON.parse(cached));
            }

            // 2️⃣ Fetch fresh from backend (Redis or DB fallback)
            const data = await fetchAllPortfolios();
            setAllMFs(data);

            // extract unique broker names
            const brokers = Object.keys(data);   // because your API returns { brokerName: {mfs:[]}}
            

            // assign colors
            const colors = {};
            brokers.forEach((b, i) => {
                colors[b] = predefinedColors[i % predefinedColors.length];
            });
            setBrokerColors(colors);

            // 3️⃣ Save to cache for instant MF view next time
            localStorage.setItem("mf_portfolio_cache", JSON.stringify(data));

        } catch (err) {
            console.error("Error fetching mutual funds:", err);
        } finally {
            setLoading(false);
        }
    };
    const predefinedColors = [
        "#e57373", "#64b5f6", "#81c784", "#ba68c8",
        "#ffb74d", "#4db6ac", "#9575cd", "#90a4ae"
    ];

    /* ============================================================
       INITIAL LOAD (unchanged)
    ============================================================ */
    useEffect(() => {
        runDailySnapshotIfNeeded();
        scheduleDailySnapshot();
        loadData();
    }, []);

    /* ============================================================
       CALCULATIONS (unchanged)
    ============================================================ */
    let totalInvested = 0;
    let currentValue = 0;
    let dayPL = 0;

    Object.values(allMFs).forEach(brokerData => {
        brokerData.mfs.forEach(fund => {
            const qty = fund.Qty;
            const avgPrice = fund.average_price;
            const ltp = fund.Ltp;
            const prevClose = fund.prev_close;

            totalInvested += avgPrice * qty;
            currentValue += ltp * qty;
            dayPL += (ltp - prevClose) * qty;
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

            {/* Dashboard */}
            <div className={style.Allstock}>
                <h2>Overall Fund Invested</h2>

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
                        onClick={loadData}
                        disabled={loading}
                        className={style.RefreshButton}
                    >
                        {loading ? "Refreshing..." : "Refresh"}
                    </button>
                </div>
                
            </div>

            {/* MF Cards */}
            <div className={style.Cards}>
                <ul className={style.StockList}>
                    {Object.entries(allMFs)
                        .flatMap(([brokerName, brokerData]) =>
                            brokerData.mfs.map((fund) => ({ fund, broker: brokerName }))
                        )
                        .map((item, index) => (
                            <li key={index}>
                                <MFsCard
                                    symbol={item.broker}
                                    name={item.fund.fund}
                                    Qty={item.fund.Qty}
                                    Ltp={item.fund.Ltp}
                                    Avg={item.fund.average_price}
                                    brokerColor={brokerColors[item.broker]}
                                />
                            </li>
                        ))}

                </ul>
            </div>
        </div>
    );
}

export default Mf;
