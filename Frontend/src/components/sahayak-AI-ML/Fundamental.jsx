import { useOutletContext } from "react-router-dom";
import { getFundamentals } from "@/Api";
import { useEffect, useState } from "react";
import style from "./Style/fundamental.module.css";

export default function Fundamental() {
  const { symbol, setLoading } = useOutletContext();
  const [data, setData] = useState({});
  const [expanded, setExpanded] = useState({});

  // ------------------------------
  // FIXED layout definitions
  // ------------------------------
  const FIELD_SECTIONS = {
    company: ["name", "symbol", "isin", "listingDate", "industry", "basicIndustry", "sector"],
    market_data: ["lastPrice", "previousClose", "open", "vwap", "dayHigh", "dayLow", "volume"],
    week: ["high", "highDate", "low", "lowDate"],
    price_band: ["lowerCircuit", "upperCircuit"],
    industry_pe: ["sectorPE", "symbolPE"],
    valuation: ["marketCap", "currentPrice", "bookValue", "priceToBook", "forwardPE", "trailingPE"],
    profitability: ["grossMargins", "operatingMargins", "profitMargins", "returnOnAssets", "returnOnEquity"],
    growth: ["revenueGrowth", "earningsGrowth"],
    financial_health: ["debtToEquity", "currentRatio", "quickRatio", "totalDebt", "totalCash"],
    dividends: ["dividendYield", "dividendRate", "payoutRatio"]
  };

  // ------------------------------
  // Cache Load on Refresh
  // ------------------------------
  useEffect(() => {
    const cached = localStorage.getItem("fundamental_cache");
    if (cached) {
     setLoading(false); 
      const parsed = JSON.parse(cached);
      setData(parsed.data);
    }
  }, []);

  // ------------------------------
  // Fetch data when OK is clicked
  // ------------------------------
  useEffect(() => {
    if (!symbol) return;

    (async () => {
      try {
        setLoading(true); 
        const res = await getFundamentals(symbol);
        const newData = res.data;

        setData(newData);

        // Save to cache
        localStorage.setItem("fundamental_cache", JSON.stringify({
          symbol,
          data: newData,
          timestamp: Date.now()
        }));
        setLoading(false); 
      } catch (err) {
        console.error("API error:", err);
      }
    })();
  }, [symbol]);

  // ------------------------------
  // Expand full text
  // ------------------------------
  const toggleExpand = (field) => {
    setExpanded((prev) => ({ ...prev, [field]: !prev[field] }));
  };
  // 🟦 Converts camelCase, PascalCase, snake_case → WORD WORD WORD
const formatLabel = (text) => {
  if (!text) return "";

  return (
    text
      // Convert camelCase → camel Case
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      // Convert snake_case → snake case
      .replace(/_/g, " ")
      // Remove extra spaces
      .replace(/\s+/g, " ")
      // Make all CAPS
      .toUpperCase()
  );
};

  // ------------------------------
  // Render one section
  // ------------------------------
  const renderSection = (title, sectionKey) => {
    const obj = data[sectionKey] || {};

    return (
      <div className={style.section}>
        <h3 className={style.sectionTitle}>{title}</h3>

        <div className={style.rowDynamic}>
          {FIELD_SECTIONS[sectionKey].map((fieldName) => {
            const value = obj[fieldName] ?? "—";
            const id = `${sectionKey}_${fieldName}`;
            const text = expanded[id] ? String(value) : String(value).slice(0, 25);

            return (
              <div key={id} className={style.card}>
                <label className={style.label}>{formatLabel(fieldName)}</label>
                <input
                  className={style.inputBox}
                  readOnly
                  onClick={() => toggleExpand(id)}
                  value={value === "—" ? "—" : text.toUpperCase() + (text.toUpperCase().length >= 25 ? "..." : "")}
                />
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className={style.wrapper}>
      {renderSection("Company Details", "company")}
      {renderSection("Market Data", "market_data")}
      {renderSection("52 Week Range", "week")}
      {renderSection("Price Band", "price_band")}
      {renderSection("Industry PE", "industry_pe")}
      {renderSection("Valuation", "valuation")}
      {renderSection("Profitability", "profitability")}
      {renderSection("Growth", "growth")}
      {renderSection("Financial Health", "financial_health")}
      {renderSection("Dividends", "dividends")}
    </div>
  );
}
