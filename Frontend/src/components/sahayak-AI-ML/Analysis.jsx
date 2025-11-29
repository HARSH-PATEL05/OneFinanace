// src/components/Sahayak/Analysis.jsx
import { useOutletContext } from "react-router-dom";
import { analyzeStock } from "@/Api";
import { useEffect, useState, useRef } from "react";
import { createChart } from "lightweight-charts/dist/lightweight-charts.esm.production.js";
import style from "./Style/analysis.module.css";

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

function formatLabel(key) {
    if (!key) return "";
    return key
        .replace(/_/g, " ")
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .toUpperCase();
}

function formatValue(value) {
    if (value === null || value === undefined) return "—";
    if (Array.isArray(value)) {
        if (value.length === 0) return "—";
        if (typeof value[0] === "object") return JSON.stringify(value);
        return value.join(", ");
    }
    if (typeof value === "object") {
        return JSON.stringify(value);
    }
    return String(value);
}

// ---------- SMALL CHART CARD ----------
function ChartCard({ title, description, type, charts, levels, onOpen }) {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current || !charts) return;

        const element = containerRef.current;
        const chart = createChart(element, {
            width: element.clientWidth,
            height: 260,
            layout: {
                background: { color: "#ffffff" },
                textColor: "#333333",
            },
            grid: {
                vertLines: { color: "#f0f0f0" },
                horzLines: { color: "#f0f0f0" },
            },
            crosshair: {
                mode: 0,
            },
            rightPriceScale: {
                borderVisible: false,
            },
            timeScale: {
                borderVisible: false,
            },
        });

        const {
            candles,
            ema20,
            ema50,
            bollinger,
            volume,
            rsi,
            macd,
            trendline,
            markers,
        } = charts || {};

        const { pivot_levels, swing_levels, multi_tf_levels } = levels || {};

        const firstTime = candles && candles.length ? candles[0].time : null;
        const lastTime =
            candles && candles.length ? candles[candles.length - 1].time : null;

        const addHorizontalLine = (value) => {
            if (firstTime == null || lastTime == null) return;
            const series = chart.addLineSeries({
                lineWidth: 1,
                lineStyle: 1,
            });
            series.setData([
                { time: firstTime, value },
                { time: lastTime, value },
            ]);
        };

        if (type === "price") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (ema20 && ema20.length) {
                const ema20Series = chart.addLineSeries({ lineWidth: 2 });
                ema20Series.setData(ema20);
            }

            if (ema50 && ema50.length) {
                const ema50Series = chart.addLineSeries({ lineWidth: 2 });
                ema50Series.setData(ema50);
            }

            if (bollinger && bollinger.middle && bollinger.middle.length) {
                const midSeries = chart.addLineSeries({ lineWidth: 1 });
                midSeries.setData(bollinger.middle);
            }

            if (trendline && trendline.length) {
                const trendSeries = chart.addLineSeries({ lineWidth: 2 });
                trendSeries.setData(trendline);
            }

            if (markers && markers.length) {
                candleSeries.setMarkers(
                    markers.map((m) => ({
                        time: m.time,
                        position: m.position === "aboveBar" ? "aboveBar" : "belowBar",
                        color: m.color === "green" ? "#16a34a" : "#ef4444",
                        shape: m.shape === "arrowUp" ? "arrowUp" : "arrowDown",
                        text: m.text,
                    }))
                );
            }
        }

        if (type === "volume") {
            const volSeries = chart.addHistogramSeries();
            if (volume && volume.length) volSeries.setData(volume);
        }

        if (type === "rsi") {
            const rsiSeries = chart.addLineSeries({ lineWidth: 2 });
            if (rsi && rsi.length) rsiSeries.setData(rsi);
        }

        if (type === "macd") {
            const macdSeries = chart.addLineSeries({ lineWidth: 2 });
            const signalSeries = chart.addLineSeries({ lineWidth: 2 });

            if (macd && macd.macd && macd.macd.length) macdSeries.setData(macd.macd);
            if (macd && macd.signal && macd.signal.length)
                signalSeries.setData(macd.signal);
        }

        if (type === "bollinger") {
            // price-based → use candles + bands
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (bollinger) {
                if (bollinger.upper && bollinger.upper.length) {
                    const upperSeries = chart.addLineSeries({ lineWidth: 1 });
                    upperSeries.setData(bollinger.upper);
                }
                if (bollinger.middle && bollinger.middle.length) {
                    const midSeries = chart.addLineSeries({ lineWidth: 2 });
                    midSeries.setData(bollinger.middle);
                }
                if (bollinger.lower && bollinger.lower.length) {
                    const lowerSeries = chart.addLineSeries({ lineWidth: 1 });
                    lowerSeries.setData(bollinger.lower);
                }
            }
        }

        if (type === "trendline") {
            // price + trendline
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (trendline && trendline.length) {
                const tSeries = chart.addLineSeries({ lineWidth: 2 });
                tSeries.setData(trendline);
            }
        }

        // ------- NEW: PIVOT / SWING / MULTI-TF CHARTS (with candles) -------
        if (type === "pivot") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (pivot_levels) {
                Object.entries(pivot_levels).forEach(([k, v]) => {
                    if (typeof v !== "number") return;
                    addHorizontalLine(v);
                });
            }
        }

        if (type === "swing") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (swing_levels) {
                if (Array.isArray(swing_levels.supports)) {
                    swing_levels.supports.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
                if (Array.isArray(swing_levels.resistances)) {
                    swing_levels.resistances.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
            }
        }

        if (type === "multiLevels") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (multi_tf_levels) {
                if (Array.isArray(multi_tf_levels.supports)) {
                    multi_tf_levels.supports.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
                if (Array.isArray(multi_tf_levels.resistances)) {
                    multi_tf_levels.resistances.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
            }
        }

        const handleResize = () => {
            if (element && element.clientWidth) {
                chart.applyOptions({ width: element.clientWidth });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, [charts, levels, type]);

    return (
        <div className={style.chartCard} onClick={onOpen}>
            <h4 className={style.chartTitle}>{title}</h4>
            <div ref={containerRef} className={style.chartCanvas} />
            {description && (
                <p className={style.chartDescription}>{description}</p>
            )}
        </div>
    );
}

// ---------- FULLSCREEN MODAL ----------
function ChartModal({ open, onClose, chartConfig, charts, levels }) {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!open || !containerRef.current || !chartConfig || !charts) return;

        const element = containerRef.current;
        const chart = createChart(element, {
            width: element.clientWidth,
            height: 520,
            layout: {
                background: { color: "#ffffff" },
                textColor: "#111827",
            },
            grid: {
                vertLines: { color: "#e5e7eb" },
                horzLines: { color: "#e5e7eb" },
            },
            crosshair: {
                mode: 0,
            },
            rightPriceScale: {
                borderVisible: false,
            },
            timeScale: {
                borderVisible: false,
            },
        });

        const { type } = chartConfig;
        const {
            candles,
            ema20,
            ema50,
            bollinger,
            volume,
            rsi,
            macd,
            trendline,
            markers,
        } = charts || {};

        const { pivot_levels, swing_levels, multi_tf_levels } = levels || {};

        const firstTime = candles && candles.length ? candles[0].time : null;
        const lastTime =
            candles && candles.length ? candles[candles.length - 1].time : null;

        const addHorizontalLine = (value) => {
            if (firstTime == null || lastTime == null) return;
            const series = chart.addLineSeries({
                lineWidth: 1,
                lineStyle: 1,
            });
            series.setData([
                { time: firstTime, value },
                { time: lastTime, value },
            ]);
        };

        if (type === "price") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (ema20 && ema20.length) {
                const e20 = chart.addLineSeries({ lineWidth: 2 });
                e20.setData(ema20);
            }
            if (ema50 && ema50.length) {
                const e50 = chart.addLineSeries({ lineWidth: 2 });
                e50.setData(ema50);
            }
            if (bollinger && bollinger.middle && bollinger.middle.length) {
                const mid = chart.addLineSeries({ lineWidth: 2 });
                mid.setData(bollinger.middle);
            }
            if (trendline && trendline.length) {
                const t = chart.addLineSeries({ lineWidth: 2 });
                t.setData(trendline);
            }
            if (markers && markers.length) {
                candleSeries.setMarkers(
                    markers.map((m) => ({
                        time: m.time,
                        position: m.position === "aboveBar" ? "aboveBar" : "belowBar",
                        color: m.color === "green" ? "#16a34a" : "#ef4444",
                        shape: m.shape === "arrowUp" ? "arrowUp" : "arrowDown",
                        text: m.text,
                    }))
                );
            }
        }

        if (type === "volume") {
            const volSeries = chart.addHistogramSeries();
            if (volume && volume.length) volSeries.setData(volume);
        }

        if (type === "rsi") {
            const rsiSeries = chart.addLineSeries({ lineWidth: 2 });
            if (rsi && rsi.length) rsiSeries.setData(rsi);
        }

        if (type === "macd") {
            const macdSeries = chart.addLineSeries({ lineWidth: 2 });
            const signalSeries = chart.addLineSeries({ lineWidth: 2 });
            if (macd && macd.macd && macd.macd.length) macdSeries.setData(macd.macd);
            if (macd && macd.signal && macd.signal.length)
                signalSeries.setData(macd.signal);
        }

        if (type === "bollinger") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (bollinger) {
                if (bollinger.upper && bollinger.upper.length) {
                    const upperSeries = chart.addLineSeries({ lineWidth: 1 });
                    upperSeries.setData(bollinger.upper);
                }
                if (bollinger.middle && bollinger.middle.length) {
                    const midSeries = chart.addLineSeries({ lineWidth: 2 });
                    midSeries.setData(bollinger.middle);
                }
                if (bollinger.lower && bollinger.lower.length) {
                    const lowerSeries = chart.addLineSeries({ lineWidth: 1 });
                    lowerSeries.setData(bollinger.lower);
                }
            }
        }

        if (type === "trendline") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (trendline && trendline.length) {
                const tSeries = chart.addLineSeries({ lineWidth: 2 });
                tSeries.setData(trendline);
            }
        }

        if (type === "pivot") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (pivot_levels) {
                Object.entries(pivot_levels).forEach(([k, v]) => {
                    if (typeof v !== "number") return;
                    addHorizontalLine(v);
                });
            }
        }

        if (type === "swing") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (swing_levels) {
                if (Array.isArray(swing_levels.supports)) {
                    swing_levels.supports.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
                if (Array.isArray(swing_levels.resistances)) {
                    swing_levels.resistances.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
            }
        }

        if (type === "multiLevels") {
            const candleSeries = chart.addCandlestickSeries();
            if (candles && candles.length) candleSeries.setData(candles);

            if (multi_tf_levels) {
                if (Array.isArray(multi_tf_levels.supports)) {
                    multi_tf_levels.supports.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
                if (Array.isArray(multi_tf_levels.resistances)) {
                    multi_tf_levels.resistances.forEach((v) => {
                        if (typeof v !== "number") return;
                        addHorizontalLine(v);
                    });
                }
            }
        }

        const handleResize = () => {
            if (element && element.clientWidth) {
                chart.applyOptions({ width: element.clientWidth });
            }
        };

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, [open, chartConfig, charts, levels]);

    if (!open || !chartConfig) return null;

    return (
        <div className={style.modalOverlay}>
            <div className={style.modalContent}>
                <button className={style.modalClose} onClick={onClose}>
                    ✕
                </button>
                <h3 className={style.modalTitle}>{chartConfig.title}</h3>
                <div ref={containerRef} className={style.modalChartCanvas} />
                {chartConfig.longDescription && (
                    <p className={style.modalDescription}>
                        {chartConfig.longDescription}
                    </p>
                )}
            </div>
        </div>
    );
}

// ---------- MAIN ANALYSIS COMPONENT ----------
export default function Analysis() {
    const outletContext = useOutletContext() || {};
    const { symbol, onLoadingChange } = outletContext;

    const [apiData, setApiData] = useState(null); // whole backend `data`
    const [activeChart, setActiveChart] = useState(null); // config for full-screen

    useEffect(() => {
        if (!symbol) return;

        let cancelled = false;

        const fetchData = async () => {
            const cacheKey = `analysis_cache_${symbol}`;
            try {
                onLoadingChange && onLoadingChange(true);

                // 1) Try cache first
                const now = Date.now();
                const cachedStr =
                    typeof window !== "undefined"
                        ? window.localStorage.getItem(cacheKey)
                        : null;

                if (cachedStr) {
                    try {
                        const cached = JSON.parse(cachedStr);
                        if (
                            cached &&
                            cached.timestamp &&
                            now - cached.timestamp < CACHE_TTL_MS &&
                            cached.data
                        ) {
                            if (!cancelled) setApiData(cached.data);
                            onLoadingChange && onLoadingChange(false);
                            return; // ✅ use cache, skip network
                        }
                    } catch {
                        // ignore parse errors, fall through to network fetch
                    }
                }

                // 2) Fallback: call API
                const res = await analyzeStock(symbol);
                const data = res.data || null;

                if (!cancelled) {
                    setApiData(data);
                    if (typeof window !== "undefined") {
                        window.localStorage.setItem(
                            cacheKey,
                            JSON.stringify({ data, timestamp: now })
                        );
                    }
                }
            } catch (err) {
                console.error("Error fetching AI analysis:", err);
            } finally {
                !cancelled && onLoadingChange && onLoadingChange(false);
            }
        };

        fetchData();

        return () => {
            cancelled = true;
        };
    }, [symbol, onLoadingChange]);

    if (!symbol) {
        return (
            <div className={style.wrapper}>
                <p className={style.placeholderText}>
                    Enter a stock name above and click OK to run AI analysis.
                </p>
            </div>
        );
    }

    if (!apiData) {
        return (
            <div className={style.wrapper}>
                <h2 className={style.title}>AI Analysis: {symbol}</h2>
                <p className={style.loading}>Running analysis...</p>
            </div>
        );
    }

    const {
        last_price,
        last_date,
        movement,
        price_prediction,
        technical,
        trend,
        levels,
        charts,
        summary,
    } = apiData;

    // ---- PREP CHART DATA ----
    const mappedCharts = charts
        ? {
            candles: charts.candles?.map((c) => ({
                time: c.time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close,
            })),
            volume: charts.volume?.map((v) => ({
                time: v.time,
                value: v.value,
            })),
            ema20: charts.ema20?.map((e) => ({ time: e.time, value: e.value })),
            ema50: charts.ema50?.map((e) => ({ time: e.time, value: e.value })),
            bollinger: charts.bollinger
                ? {
                    upper: charts.bollinger.upper?.map((p) => ({
                        time: p.time,
                        value: p.value,
                    })),
                    middle: charts.bollinger.middle?.map((p) => ({
                        time: p.time,
                        value: p.value,
                    })),
                    lower: charts.bollinger.lower?.map((p) => ({
                        time: p.time,
                        value: p.value,
                    })),
                }
                : null,
            rsi: charts.rsi?.map((r) => ({ time: r.time, value: r.value })),
            macd: charts.macd
                ? {
                    macd: charts.macd.macd?.map((m) => ({
                        time: m.time,
                        value: m.value,
                    })),
                    signal: charts.macd.signal?.map((m) => ({
                        time: m.time,
                        value: m.value,
                    })),
                }
                : null,
            trendline: charts.trendline?.map((t) => ({
                time: t.time,
                value: t.value,
            })),
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

    // 3 charts per row config
    const chartConfigs = [
        {
            id: "price",
            title: "Price + EMA + Trend",
            type: "price",
            description:
                "Candlestick chart with EMA20, EMA50, Bollinger midline and regression trendline. Arrows mark bullish/bearish events driving the prediction.",
            longDescription:
                "This primary chart overlays short & medium EMAs, a regression trendline, and key breakout/breakdown markers. It visually supports the movement and price prediction models.",
        },
        {
            id: "volume",
            title: "Volume Profile",
            type: "volume",
            description:
                "Daily traded volume to confirm strength or weakness behind price swings.",
            longDescription:
                "Rising price with rising volume generally confirms trend strength, while price moves on weak volume are more likely to fade.",
        },
        {
            id: "rsi",
            title: "RSI Momentum",
            type: "rsi",
            description:
                "RSI oscillation to detect overbought/oversold and momentum shifts.",
            longDescription:
                "RSI around 50 supports ongoing trend; sharp moves to 70+ or below 30 highlight exhaustion and possible reversals.",
        },
        {
            id: "macd",
            title: "MACD & Signal",
            type: "macd",
            description:
                "MACD vs signal line to visualize bullish/bearish momentum crossovers.",
            longDescription:
                "MACD crossovers combined with trend direction and volume alignment are used by the model to boost confidence in a move.",
        },
        {
            id: "bollinger",
            title: "Bollinger Bands + Price",
            type: "bollinger",
            description:
                "Candles inside volatility bands to reveal squeezes, expansions and mean reversion.",
            longDescription:
                "Band squeezes can precede strong moves; price hugging outer bands shows volatility expansion, while moves back to the mid-band show cooling.",
        },
        {
            id: "trendline",
            title: "Regression Trendline",
            type: "trendline",
            description:
                "Price candles with a smooth regression-style trendline summarizing direction.",
            longDescription:
                "Helps visualize the core uptrend/downtrend over the chosen window and validates the Strong Uptrend/Weak/Sideways labels.",
        },
        {
            id: "pivot",
            title: "Pivot Levels on Price",
            type: "pivot",
            description:
                "Pivot, S/R levels plotted directly on candles for intraday reference.",
            longDescription:
                "Classical floor pivots (P, S1–S3, R1–R3) turn into potential reaction zones. Clusters around recent highs/lows act as strong magnets/barriers.",
        },
        {
            id: "swing",
            title: "Swing Support & Resistance",
            type: "swing",
            description:
                "Swing-based supports and resistances projected as horizontal levels over price.",
            longDescription:
                "Identifies recent swing highs/lows that price has respected. Breaks and retests of these levels align with the breakout markers on the main chart.",
        },
        {
            id: "multiLevels",
            title: "Multi-Timeframe Levels",
            type: "multiLevels",
            description:
                "Combined supports/resistances from multiple timeframes drawn over candles.",
            longDescription:
                "When multiple timeframes agree on the same zone, those levels become high conviction areas for reversals, bounces or breakouts.",
        },
    ];

    function formatNumber(value) {
        if (value === null || value === undefined) return "—";

        // If array → format each value inside array
        if (Array.isArray(value)) {
            return value.map((v) =>
                typeof v === "number" ? v.toFixed(2) : v
            );
        }

        // If single number
        if (typeof value === "number") {
            return value.toFixed(2);
        }

        return value;
    }

    const renderSection = (title, obj) => {
        if (!obj) return null;

        return (
            <div className={style.section}>
                <h3 className={style.sectionTitle}>{title}</h3>
                <div className={style.fieldGrid}>
                    {Object.entries(obj).map(([key, value]) => (
                        <div key={key} className={style.card}>
                            <label className={style.label}>{formatLabel(key)}</label>
                            <input
                                readOnly
                                className={style.inputBox}
                                value={formatValue(value)}
                                title={formatValue(value)}
                            />
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className={style.wrapper}>
            <h2 className={style.title}>AI ANALYSIS: {symbol}</h2>

            {/* Overview Row */}
            <div className={style.section}>
                <h3 className={style.sectionTitle}>OVERVIEW</h3>
                <div className={style.fieldGrid}>
                    <div className={style.card}>
                        <label className={style.label}>LAST PRICE</label>
                        <input
                            readOnly
                            className={style.inputBox}
                            value={last_price ?? "—"}
                        />
                    </div>
                    <div className={style.card}>
                        <label className={style.label}>LAST DATE</label>
                        <input
                            readOnly
                            className={style.inputBox}
                            value={last_date ?? "—"}
                        />
                    </div>
                    <div className={style.card}>
                        <label className={style.label}>MOVEMENT</label>
                        <input
                            readOnly
                            className={style.inputBox}
                            value={
                                movement
                                    ? `${movement.movement_prediction} (${movement.movement_confidence}% CONF)`
                                    : "—"
                            }
                        />
                    </div>
                    <div className={style.card}>
                        <label className={style.label}>PRICE PREDICTION</label>
                        <input
                            readOnly
                            className={style.inputBox}
                            value={
                                price_prediction
                                    ? `${price_prediction.predicted_close} (${price_prediction.direction}, ${price_prediction.confidence}% CONF)`
                                    : "—"
                            }
                        />
                    </div>
                    <div className={style.card}>
                        <label className={style.label}>TREND</label>
                        <input
                            readOnly
                            className={style.inputBox}
                            value={
                                trend
                                    ? `${trend.trend} (S:${trend.short_term}, M:${trend.medium_term}, L:${trend.long_term})`
                                    : "—"
                            }
                        />
                    </div>
                </div>
            </div>

            {/* Detail sections (still there for numeric reference) */}
            {movement &&
                renderSection("MOVEMENT PREDICTION DETAILS", {
                    movement_prediction: movement.movement_prediction,
                    movement_confidence: movement.movement_confidence,
                    votes_RF: movement.votes?.RF,
                    votes_GB: movement.votes?.GB,
                    votes_XGB: movement.votes?.XGB,
                })}

            {price_prediction &&
                renderSection("PRICE PREDICTION DETAILS", {
                    last_close: price_prediction.last_close,
                    predicted_return: price_prediction.predicted_return,
                    predicted_close: price_prediction.predicted_close,
                    direction: price_prediction.direction,
                    confidence: price_prediction.confidence,
                    models_used: price_prediction.models_used,
                })}

            {technical && renderSection("TECHNICAL SNAPSHOT", technical)}
            {trend && renderSection("TREND SNAPSHOT", trend)}

            {levels?.pivot_levels &&
                renderSection("PIVOT LEVELS (NUMERIC)", levels.pivot_levels)}

            {levels?.swing_levels &&
                renderSection("SWING LEVELS (NUMERIC)", {
                    supports: formatNumber(levels.swing_levels.supports),
                    resistances: formatNumber(levels.swing_levels.resistances),
                })}


            {levels?.multi_tf_levels &&
                renderSection("MULTI TIMEFRAME LEVELS (NUMERIC)", {
                    supports: formatNumber(levels.multi_tf_levels.supports),
                    resistances: formatNumber(levels.multi_tf_levels.resistances),
                })}


            {/* Charts Grid: strictly 3 per row via CSS */}
            {mappedCharts && (
                <div className={style.section}>
                    <h3 className={style.sectionTitle}>CHARTS</h3>
                    <div className={style.chartGrid}>
                        {chartConfigs.map((cfg) => (
                            <ChartCard
                                key={cfg.id}
                                title={cfg.title}
                                description={cfg.description}
                                type={cfg.type}
                                charts={mappedCharts}
                                levels={levelPayload}
                                onOpen={() => setActiveChart(cfg)}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Summary at bottom */}
            <div className={style.section}>
                <h3 className={style.sectionTitle}>AI SUMMARY</h3>
                <textarea
                    className={style.summaryBox}
                    readOnly
                    value={summary || "—"}
                />
            </div>

            {/* Fullscreen chart modal */}
            <ChartModal
                open={!!activeChart}
                onClose={() => setActiveChart(null)}
                chartConfig={activeChart}
                charts={mappedCharts}
                levels={levelPayload}
            />
        </div>
    );
}
