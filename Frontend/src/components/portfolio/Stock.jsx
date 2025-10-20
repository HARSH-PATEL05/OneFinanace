import { useState, useEffect } from "react";
import style from './Style/Stock.module.css';
import StocksCard from './Card';
import { fetchAllPortfolios } from "@/Api";

function Stock() {
    const [allHoldings, setAllHoldings] = useState({});
    const [loading, setLoading] = useState(false);

    const loadData = async () => {
        setLoading(true);
        try {
            const data = await fetchAllPortfolios();
            setAllHoldings(data);
        } catch (err) {
            console.error("Error fetching holdings:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    // Dashboard calculations
    let totalInvested = 0;
    let currentValue = 0;
    let dayPL = 0;

    Object.values(allHoldings).forEach(brokerData => {
        brokerData.holdings.forEach(stock => {
            const qty = stock.Qty;
            const avgPrice = stock.average_price;
            const ltp = stock.Ltp;           // replace with live price later
            const prevClose = stock.prev_close || ltp; // placeholder for day P/L

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

            <div className={style.Allstock}>
                <h2>Overall Investment</h2>
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


            <div className={style.Cards}>

                <ul className={style.List}>
                    {Object.values(allHoldings)
                        .flatMap(brokerData => brokerData.holdings)
                        .map((stock, index) => (
                            <li key={index}>
                                <StocksCard
                                    name={stock.name}
                                    Qty={stock.Qty}
                                    Ltp={stock.Ltp}
                                    Avg={stock.average_price}
                                />
                            </li>
                        ))}
                </ul>
            </div>
        </div>
    );
}

export default Stock;
