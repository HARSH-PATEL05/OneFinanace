// src/components/Sahayak/Analysis.jsx
import { useOutletContext } from "react-router-dom";
import { analyzeStock } from "@/Api";
import { useEffect, useState, useRef } from "react";
import { createChart } from "lightweight-charts/dist/lightweight-charts.esm.production.js";
import style from "./Style/analysis.module.css";

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

function formatLabel(key) {
    if (!key) return "";
    return key.replace(/_/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2").toUpperCase();
}

function formatValue(value) {
    if (value === null || value === undefined) return "—";
    if (Array.isArray(value)) {
        if (value.length === 0) return "—";
        if (typeof value[0] === "object") return JSON.stringify(value);
        return value.join(", ");
    }
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}

/* ======================================================================================
   ✦ CHART CARD COMPONENT — (UNCHANGED, just placed fully)
   ====================================================================================== */
function ChartCard({ title, description, type, charts, levels, onOpen }) {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current || !charts) return;

        const element = containerRef.current;
        const chart = createChart(element, {
            width: element.clientWidth,
            height: 260,
            layout: { background: { color: "#ffffff" }, textColor: "#333" },
            grid: { vertLines: { color: "#f0f0f0" }, horzLines: { color: "#f0f0f0" } },
            crosshair: { mode: 0 },
            rightPriceScale: { borderVisible: false },
            timeScale: { borderVisible: false },
        });

        const { candles, ema20, ema50, bollinger, volume, rsi, macd, trendline, markers } = charts || {};
        const { pivot_levels, swing_levels, multi_tf_levels } = levels || {};

        const firstTime = candles?.[0]?.time;
        const lastTime = candles?.[candles.length - 1]?.time;

        const addLine = (value) => {
            if (!firstTime || !lastTime) return;
            const s = chart.addLineSeries({ lineWidth: 1 });
            s.setData([{ time: firstTime, value }, { time: lastTime, value }]);
        };

        // --- ALL CHART TYPES (unchanged)
        if (type === "price") {
            const candle = chart.addCandlestickSeries();
            candles && candle.setData(candles);
            ema20 && chart.addLineSeries({ lineWidth: 2 }).setData(ema20);
            ema50 && chart.addLineSeries({ lineWidth: 2 }).setData(ema50);
            bollinger?.middle && chart.addLineSeries({ lineWidth: 1 }).setData(bollinger.middle);
            trendline && chart.addLineSeries({ lineWidth: 2 }).setData(trendline);
            markers &&
                candle.setMarkers(
                    markers.map((m) => ({
                        time: m.time,
                        position: m.position === "aboveBar" ? "aboveBar" : "belowBar",
                        color: m.color === "green" ? "#16a34a" : "#ef4444",
                        shape: m.shape === "arrowUp" ? "arrowUp" : "arrowDown",
                        text: m.text,
                    }))
                );
        }

        if (type === "volume") {
            const v = chart.addHistogramSeries();
            volume && v.setData(volume);
        }

        if (type === "rsi") {
            const r = chart.addLineSeries({ lineWidth: 2 });
            rsi && r.setData(rsi);
        }

        if (type === "macd") {
            const m = chart.addLineSeries({ lineWidth: 2 });
            const s = chart.addLineSeries({ lineWidth: 2 });
            macd?.macd && m.setData(macd.macd);
            macd?.signal && s.setData(macd.signal);
        }

        if (type === "bollinger") {
            const c = chart.addCandlestickSeries();
            candles && c.setData(candles);
            bollinger?.upper && chart.addLineSeries().setData(bollinger.upper);
            bollinger?.middle && chart.addLineSeries({ lineWidth: 2 }).setData(bollinger.middle);
            bollinger?.lower && chart.addLineSeries().setData(bollinger.lower);
        }

        if (type === "trendline") {
            const c = chart.addCandlestickSeries();
            candles && c.setData(candles);
            trendline && chart.addLineSeries({ lineWidth: 2 }).setData(trendline);
        }

        if (type === "pivot") {
            const c = chart.addCandlestickSeries();
            candles && c.setData(candles);
            pivot_levels && Object.values(pivot_levels).forEach((v) => typeof v === "number" && addLine(v));
        }

        if (type === "swing") {
            const c = chart.addCandlestickSeries();
            candles && c.setData(candles);
            swing_levels?.supports?.forEach((v) => addLine(v));
            swing_levels?.resistances?.forEach((v) => addLine(v));
        }

        if (type === "multiLevels") {
            const c = chart.addCandlestickSeries();
            candles && c.setData(candles);
            multi_tf_levels?.supports?.forEach((v) => addLine(v));
            multi_tf_levels?.resistances?.forEach((v) => addLine(v));
        }

        const resize = () => chart.applyOptions({ width: element.clientWidth });
        window.addEventListener("resize", resize);
        return () => {
            window.removeEventListener("resize", resize);
            chart.remove();
        };
    }, [charts, levels, type]);

    return (
        <div className={style.chartCard} onClick={onOpen}>
            <h4 className={style.chartTitle}>{title}</h4>
            <div ref={containerRef} className={style.chartCanvas} />
            {description && <p className={style.chartDescription}>{description}</p>}
        </div>
    );
}

/* ======================================================================================
   ✦ CHART MODAL (FULL SCREEN) — NOW INCLUDED COMPLETELY
   ====================================================================================== */
function ChartModal({ open, onClose, chartConfig, charts, levels }) {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!open || !containerRef.current || !chartConfig || !charts) return;

        const element = containerRef.current;
        const chart = createChart(element, {
            width: element.clientWidth,
            height: 520,
            layout: { background: { color: "#fff" }, textColor: "#111" },
            grid: { vertLines: { color: "#e5e7eb" }, horzLines: { color: "#e5e7eb" } },
            crosshair: { mode: 0 },
            rightPriceScale: { borderVisible: false },
            timeScale: { borderVisible: false },
        });

        const { type } = chartConfig;
        const { candles, ema20, ema50, bollinger, volume, rsi, macd, trendline, markers } = charts;
        const { pivot_levels, swing_levels, multi_tf_levels } = levels;

        const first = candles?.[0]?.time;
        const last = candles?.[candles.length - 1]?.time;

        const addLine = (value) => {
            if (!first || !last) return;
            chart.addLineSeries({ lineWidth: 1 }).setData([
                { time: first, value },
                { time: last, value },
            ]);
        };

        if (type === "price") {
            const c = chart.addCandlestickSeries();
            c.setData(candles);
            ema20 && chart.addLineSeries({ lineWidth: 2 }).setData(ema20);
            ema50 && chart.addLineSeries({ lineWidth: 2 }).setData(ema50);
            bollinger?.middle && chart.addLineSeries({ lineWidth: 1 }).setData(bollinger.middle);
            trendline && chart.addLineSeries({ lineWidth: 2 }).setData(trendline);
            markers &&
                c.setMarkers(
                    markers.map((m) => ({
                        time: m.time,
                        text: m.text,
                        color: m.color === "green" ? "#16a34a" : "#ef4444",
                        shape: m.shape === "arrowUp" ? "arrowUp" : "arrowDown",
                        position: m.position === "aboveBar" ? "aboveBar" : "belowBar",
                    }))
                );
        }

        if (type === "volume") {
            const s = chart.addHistogramSeries();
            s.setData(volume);
        }

        if (type === "rsi") chart.addLineSeries({ lineWidth: 2 }).setData(rsi);

        if (type === "macd") {
            chart.addLineSeries({ lineWidth: 2 }).setData(macd.macd);
            chart.addLineSeries({ lineWidth: 2 }).setData(macd.signal);
        }

        if (type === "bollinger") {
            const c = chart.addCandlestickSeries();
            c.setData(candles);
            bollinger?.upper && chart.addLineSeries().setData(bollinger.upper);
            bollinger?.middle && chart.addLineSeries({ lineWidth: 2 }).setData(bollinger.middle);
            bollinger?.lower && chart.addLineSeries().setData(bollinger.lower);
        }

        if (type === "trendline") {
            const c = chart.addCandlestickSeries();
            c.setData(candles);
            chart.addLineSeries({ lineWidth: 2 }).setData(trendline);
        }

        if (type === "pivot") {
            const c = chart.addCandlestickSeries();
            c.setData(candles);
            pivot_levels && Object.values(pivot_levels).forEach((v) => typeof v === "number" && addLine(v));
        }

        if (type === "swing") {
            const c = chart.addCandlestickSeries();
            c.setData(candles);
            swing_levels.supports?.forEach((v) => addLine(v));
            swing_levels.resistances?.forEach((v) => addLine(v));
        }

        if (type === "multiLevels") {
            const c = chart.addCandlestickSeries();
            c.setData(candles);
            multi_tf_levels.supports?.forEach((v) => addLine(v));
            multi_tf_levels.resistances?.forEach((v) => addLine(v));
        }

        const resize = () => chart.applyOptions({ width: element.clientWidth });
        window.addEventListener("resize", resize);

        return () => {
            window.removeEventListener("resize", resize);
            chart.remove();
        };
    }, [open, chartConfig, charts, levels]);

    if (!open) return null;

    return (
        <div className={style.modalOverlay}>
            <div className={style.modalContent}>
                <button className={style.modalClose} onClick={onClose}>✕</button>
                <h3 className={style.modalTitle}>{chartConfig.title}</h3>
                <div ref={containerRef} className={style.modalChartCanvas} />
                {chartConfig.longDescription && (
                    <p className={style.modalDescription}>{chartConfig.longDescription}</p>
                )}
            </div>
        </div>
    );
}

/* ======================================================================================
   ✦ MAIN ANALYSIS COMPONENT — CACHE + UI LOAD FIXED
   ====================================================================================== */
export default function Analysis() {
    let { symbol, onLoadingChange } = useOutletContext() || {};

    // Restore last symbol if empty
    if (!symbol) {
        const saved = localStorage.getItem("last_symbol");
        if (saved) symbol = saved;
    } else {
        localStorage.setItem("last_symbol", symbol);
    }

    // Load global cache immediately
    const [apiData, setApiData] = useState(() => {
        const globalCache = localStorage.getItem("analysis_cache_latest");
        if (globalCache) {
            try {
                return JSON.parse(globalCache).data;
            } catch { }
        }
        return null;
    });

    const [activeChart, setActiveChart] = useState(null);

    // Main fetch logic
    useEffect(() => {
        if (!symbol) return;

        onLoadingChange?.(true);

        const key = `analysis_cache_${symbol}`;
        const cachedStr = localStorage.getItem(key);
        const now = Date.now();
        let cancelled = false;

        async function load() {
            if (cachedStr) {
                try {
                    const cached = JSON.parse(cachedStr);
                    if (now - cached.timestamp < CACHE_TTL_MS) {
                        !cancelled && setApiData(cached.data);
                        onLoadingChange?.(false);
                        return;
                    }
                } catch { }
            }

            try {
                const res = await analyzeStock(symbol);
                if (!cancelled) {
                    setApiData(res.data);

                    localStorage.setItem(key, JSON.stringify({ data: res.data, timestamp: now }));
                    localStorage.setItem("analysis_cache_latest", JSON.stringify({ symbol, data: res.data }));
                }
            } catch (err) {
                console.error("Analysis error:", err);
            } finally {
                !cancelled && onLoadingChange?.(false);
            }
        }

        load();
        return () => (cancelled = true);
    }, [symbol]);

    // Show placeholder only if no cache AND no symbol
    if (!symbol && !apiData)
        return (
            <div className={style.wrapper}>
                <p className={style.placeholderText}>Enter a stock name above and click OK to run AI analysis.</p>
            </div>
        );

    if (!apiData)
        return (
            <div className={style.wrapper}>
                <h2 className={style.title}>AI Analysis: {symbol}</h2>
                <p className={style.loading}>Running analysis...</p>
            </div>
        );

    /* ==================================================================================
       ✦ NOTHING BELOW THIS CHANGED (your full UI rendering)
       ================================================================================== */

    const { last_price, last_date, movement, price_prediction, technical, trend, levels, charts, summary } = apiData;

    const mappedCharts = charts
        ? {
            candles: charts.candles?.map((c) => ({ time: c.time, open: c.open, high: c.high, low: c.low, close: c.close })),
            volume: charts.volume?.map((v) => ({ time: v.time, value: v.value })),
            ema20: charts.ema20?.map((e) => ({ time: e.time, value: e.value })),
            ema50: charts.ema50?.map((e) => ({ time: e.time, value: e.value })),
            bollinger: charts.bollinger
                ? {
                    upper: charts.bollinger.upper?.map((p) => ({ time: p.time, value: p.value })),
                    middle: charts.bollinger.middle?.map((p) => ({ time: p.time, value: p.value })),
                    lower: charts.bollinger.lower?.map((p) => ({ time: p.time, value: p.value })),
                }
                : null,
            rsi: charts.rsi?.map((r) => ({ time: r.time, value: r.value })),
            macd: charts.macd
                ? {
                    macd: charts.macd.macd?.map((m) => ({ time: m.time, value: m.value })),
                    signal: charts.macd.signal?.map((m) => ({ time: m.time, value: m.value })),
                }
                : null,
            trendline: charts.trendline?.map((t) => ({ time: t.time, value: t.value })),
            markers: charts.markers,
        }
        : null;

    const pivotLevels = levels?.pivot_levels;
    const swingLevels = levels?.swing_levels;
    const multiTfLevels = levels?.multi_tf_levels;

    const levelPayload = {
        pivot_levels: pivotLevels,
        swing_levels: swingLevels,
        multi_tf_levels: multiTfLevels,
    };

    function formatNumber(value) {
        if (value == null) return "—";
        if (Array.isArray(value)) return value.map((v) => (typeof v === "number" ? v.toFixed(2) : v));
        if (typeof value === "number") return value.toFixed(2);
        return value;
    }

    const renderSection = (title, obj) => {
        if (!obj) return null;
        return (
            <div className={style.section}>
                <h3 className={style.sectionTitle}>{title}</h3>
                <div className={style.fieldGrid}>
                    {Object.entries(obj).map(([k, v]) => (
                        <div key={k} className={style.card}>
                            <label className={style.label}>{formatLabel(k)}</label>
                            <input readOnly className={style.inputBox} value={formatValue(v)} title={formatValue(v)} />
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    const chartConfigs = [
        {
            id: "price", title: "Price + EMA + Trend", type: "price", description: "Candlestick chart with EMA20, EMA50, Bollinger midline and regression trend.", longDescription:
                "This is the primary price action chart. It combines candlesticks with EMA20 and EMA50 to show short- and medium-term trend direction. "
                + "The regression trendline helps identify the overall price slope. Breakout / breakdown markers highlight major trend events. "
                + "Useful for understanding momentum, trend strength, and possible reversal signals."
        },
        {
            id: "volume", title: "Volume Profile", type: "volume", description: "Daily traded volume", longDescription:
                "Volume measures the strength behind a price move. Rising price with strong volume indicates strong market participation. "
                + "Falling price on low volume suggests a weak sell-off. Spikes in volume often precede major breakouts or breakdowns."
        },
        {
            id: "rsi", title: "RSI Momentum", type: "rsi", description: "RSI momentum shifts", longDescription:
                "RSI oscillates between 0 and 100. Values above 70 indicate overbought conditions, while values below 30 indicate oversold conditions. "
                + "RSI divergence (price making new highs while RSI does not) often signals an upcoming trend reversal. "
                + "Useful for timing entries during pullbacks and identifying exhaustion points."
        },
        {
            id: "macd", title: "MACD & Signal", type: "macd", description: "MACD crossovers", longDescription:
                "MACD consists of the MACD line and the Signal line. A bullish crossover happens when MACD crosses above Signal, indicating upward momentum. "
                + "A bearish crossover occurs when MACD falls below Signal. "
                + "MACD also shows the strength of momentum through histogram distance. "
                + "Helps confirm trend direction and catch early momentum shifts."
        },
        {
            id: "bollinger", title: "Bollinger Bands", type: "bollinger", description: "Volatility squeeze", longDescription:
                "Bollinger Bands measure volatility using standard deviations. When the bands squeeze tightly, volatility is low and a major breakout may be coming. "
                + "When price rides the upper band, it usually indicates a strong uptrend. "
                + "Touching the lower band can indicate mean reversion or a downtrend continuation."
        },
        {
            id: "trendline", title: "Regression Trendline", type: "trendline", description: "Smoothed direction", longDescription:
                "The regression trendline smooths out price fluctuations and shows the dominant trend direction. "
                + "It helps eliminate noise and gives a clear view of price slope. "
                + "Useful for long-term trend analysis and identifying whether the market is in uptrend, downtrend, or sideways."
        },
        {
            id: "pivot", title: "Pivot Levels", type: "pivot", description: "Pivots on candles", longDescription:
                "Pivot points are classical levels used by traders to identify potential reversal or breakout zones. "
                + "P (pivot) is the central reference point, while S1–S3 are support levels and R1–R3 are resistance levels. "
                + "When price approaches any pivot, strong reaction is likely."
        },
        {
            id: "swing", title: "Swing Levels", type: "swing", description: "Swing supports/resistances", longDescription:
                "Swing levels are created from recent swing highs and swing lows. "
                + "Swing highs act as resistance, and swing lows act as support. "
                + "Breaks of swing levels usually indicate a strong trend continuation, while bounces indicate reversals."
        },
        {
            id: "multiLevels", title: "Multi-Timeframe Levels", type: "multiLevels", description: "Multi-TF levels", longDescription:
                "Multi-timeframe support and resistance levels combine data from different timeframes (daily, weekly, monthly). "
                + "Overlapping levels from many timeframes become extremely strong zones. "
                + "Traders use these areas to detect high-probability reversal or breakout points."
        },
    ];


    return (
        <div className={style.wrapper}>
            <h2 className={style.title}>AI ANALYSIS: {symbol}</h2>
                
            {/* Overview */}
            <div className={style.section}>
                <h3 className={style.sectionTitle}>OVERVIEW</h3>
                <div className={style.fieldGrid}>
                    <div className={style.card}><label className={style.label}>LAST PRICE</label><input readOnly className={style.inputBox} value={last_price ?? "—"} /></div>
                    <div className={style.card}><label className={style.label}>LAST DATE</label><input readOnly className={style.inputBox} value={last_date ?? "—"} /></div>
                    <div className={style.card}><label className={style.label}>MOVEMENT</label><input readOnly className={style.inputBox} value={movement ? `${movement.movement_prediction} (${movement.movement_confidence}% CONF)` : "—"} /></div>
                    <div className={style.card}><label className={style.label}>PRICE PREDICTION</label><input readOnly className={style.inputBox} value={price_prediction ? `${price_prediction.predicted_close} (${price_prediction.direction}, ${price_prediction.confidence}% CONF)` : "—"} /></div>
                    <div className={style.card}><label className={style.label}>TREND</label><input readOnly className={style.inputBox} value={trend ? `${trend.trend} (S:${trend.short_term}, M:${trend.medium_term}, L:${trend.long_term})` : "—"} /></div>
                </div>
            </div>

            {movement && renderSection("MOVEMENT PREDICTION DETAILS", {
                movement_prediction: movement.movement_prediction,
                movement_confidence: movement.movement_confidence,
                votes_RF: movement.votes?.RF,
                votes_GB: movement.votes?.GB,
                votes_XGB: movement.votes?.XGB,
            })}

            {price_prediction && renderSection("PRICE PREDICTION DETAILS", {
                last_close: price_prediction.last_close,
                predicted_return: price_prediction.predicted_return,
                predicted_close: price_prediction.predicted_close,
                direction: price_prediction.direction,
                confidence: price_prediction.confidence,
                models_used: price_prediction.models_used,
            })}

            {technical && renderSection("TECHNICAL SNAPSHOT", technical)}
            {trend && renderSection("TREND SNAPSHOT", trend)}

            {levels?.pivot_levels && renderSection("PIVOT LEVELS (NUMERIC)", levels.pivot_levels)}

            {levels?.swing_levels && renderSection("SWING LEVELS (NUMERIC)", {
                supports: formatNumber(swingLevels?.supports),
                resistances: formatNumber(swingLevels?.resistances),
            })}

            {levels?.multi_tf_levels && renderSection("MULTI TIMEFRAME LEVELS (NUMERIC)", {
                supports: formatNumber(multiTfLevels?.supports),
                resistances: formatNumber(multiTfLevels?.resistances),
            })}

            {/* Charts */}
            {mappedCharts && (
                <div className={style.section}>
                    <h3 className={style.sectionTitle}>CHARTS</h3>
                    <div className={style.chartGrid}>
                        {chartConfigs.map((c) => (
                            <ChartCard
                                key={c.id}
                                title={c.title}
                                description={c.description}
                                type={c.type}
                                charts={mappedCharts}
                                levels={levelPayload}
                                onOpen={() => setActiveChart(c)}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Summary */}
            <div className={style.section}>
                <h3 className={style.sectionTitle}>AI SUMMARY</h3>
                <textarea className={style.summaryBox} readOnly value={summary || "—"} />
            </div>

            {/* Modal */}
            <ChartModal open={!!activeChart} onClose={() => setActiveChart(null)} chartConfig={activeChart} charts={mappedCharts} levels={levelPayload} />
        </div>
    );
}
