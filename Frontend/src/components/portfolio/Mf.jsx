import { useState, useEffect } from "react";
import MFsCard from './Card';
import style from './Style/Stock.module.css';
import { fetchAllPortfolios } from "@/Api";

function Mf() {
    const [allMFs, setAllMFs] = useState({});
    const [loading, setLoading] = useState(false);

    // Fetch all brokers' MF data
    const loadData = async () => {
        setLoading(true);
        try {
            const data = await fetchAllPortfolios();
            setAllMFs(data);
        } catch (err) {
            console.error("Error fetching mutual funds:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    // Calculate dashboard values
    let totalInvested = 0;
    let currentValue = 0;
    let dayPL = 0;

    Object.values(allMFs).forEach(brokerData => {
        brokerData.mfs.forEach(fund => {
          
            const qty = fund.Qty;
            const avgPrice = fund.average_price;
            const ltp = fund.Ltp;          // replace with live price later
            const prevClose = fund.prev_ltp || ltp; // placeholder for day P/L

            totalInvested += avgPrice * qty;
            currentValue += ltp * qty;
            dayPL += (ltp - prevClose) * qty;
        });
    });

    const overallPL = currentValue - totalInvested;
    const overallPLPercent = totalInvested > 0 ? (overallPL / totalInvested) * 100 : 0;
    const dayPLPercent = currentValue > 0 ? (dayPL / currentValue) * 100 : 0;

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
                        <h4>{currentValue.toFixed(2)}</h4>
                    </div>
                    <div className={style.Dashboard}>
                        <h3>Overall P/L</h3>
                        <div className={style.flex}>
                            <h4>{overallPL.toFixed(2)}</h4>
                            <h4>{overallPLPercent.toFixed(2)}%</h4>
                        </div>
                    </div>
                    <div className={style.Dashboard}>
                        <h3>Day P/L</h3>
                        <div className={style.flex}>
                            <h4>{dayPL.toFixed(2)}</h4>
                            <h4>{dayPLPercent.toFixed(2)}%</h4>
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

            {/* Mutual Funds Cards */}
            <div className={style.Cards}>

                <ul className={style.StockList}>
                    {Object.values(allMFs)
                        .flatMap(brokerData => brokerData.mfs)
                        .map((Fund, index) => (
                            <li key={index}>
                                <MFsCard
                                    name={Fund.fund}
                                    Qty={Fund.Qty}
                                    Ltp={Fund.Ltp}
                                    Avg={Fund.average_price}
                                />
                            </li>
                        ))}
                </ul>
            </div>
        </div>
    );
}

export default Mf;
