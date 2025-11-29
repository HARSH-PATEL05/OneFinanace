import style from './Style/Card.module.css';

function StocksCard({ symbol="none",name, Avg, Qty, Ltp, brokerColor = "white" }) {

  const invested = parseFloat((Avg * Qty).toFixed(2));
  const current_overall_price_present = parseFloat((Qty * Ltp).toFixed(2));
  const overall_pl = parseFloat((current_overall_price_present - invested).toFixed(2));
  const overall_pl_per = parseFloat(((current_overall_price_present / invested) * 100).toFixed(2));

  const formatted_overall_pl = (overall_pl > 0 ? "+" : "") + overall_pl;
  const formatted_overall_pl_per = (overall_pl > 0 ? "+" : "") + (overall_pl_per - 100).toFixed(2);

  // ⭐ decide color class
  const plColorClass =
    overall_pl > 0 ? style.green :
      overall_pl < 0 ? style.red :
        "";
  
  return (
    <div className={style.Card}>

      <div className={style.itemdiv}>
        <div className={style.item}>
          Qty.{Qty}<span></span>Avg.{Avg}
        </div>
        <div className={style.priceRow}>
          <div className={style.brokerColorBox} style={{ backgroundColor: brokerColor }}>{symbol.slice(0, 10).toUpperCase()}</div>

        </div>
        {/* ⭐ APPLY COLOR HERE */}
        <div className={`${style.item} ${plColorClass}`}>
          {formatted_overall_pl_per}%
        </div>
      </div>

      <div className={style.itemdiv}>
        <div className={style.item}><h4>{name}</h4></div>

        {/* ⭐ APPLY COLOR HERE */}
        <div className={`${style.item} ${plColorClass}`}>
          {formatted_overall_pl}
        </div>
      </div>

      <div className={style.itemdiv}>
        <div className={style.item}>Invested {invested}</div>
        <div className={style.item}>LTP {Ltp}</div>
      </div>

    </div>
  );
}

export default StocksCard;
