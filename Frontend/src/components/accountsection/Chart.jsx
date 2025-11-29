// Chart.jsx (production-ready, A2: precomputed cached datasets, optimized)
// PLACE THIS FILE EXACTLY AS IS — ONLY CHANGE IS RELOAD FIX.

import { useEffect, useMemo, useState, useRef } from "react";
import style from "./Style/Chart.module.css";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

import { listAccounts, fetchTransactions } from "@/Api";

/* ---------- Constants & Helpers ---------- */
const MONTHS = [
  { idx: 0, label: "Jan" }, { idx: 1, label: "Feb" }, { idx: 2, label: "Mar" },
  { idx: 3, label: "Apr" }, { idx: 4, label: "May" }, { idx: 5, label: "Jun" },
  { idx: 6, label: "Jul" }, { idx: 7, label: "Aug" }, { idx: 8, label: "Sep" },
  { idx: 9, label: "Oct" }, { idx: 10, label: "Nov" }, { idx: 11, label: "Dec" }
];

function startOfDay(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; }
function endOfDay(d) { const x = new Date(d); x.setHours(23, 59, 59, 999); return x; }

function rupee(v) { if (v == null || Number.isNaN(Number(v))) return "₹0"; return "₹" + Number(v).toLocaleString(); }

function normalizeMode(m) {
  if (m == null) return "OTHER";
  const s = String(m).trim();
  if (!s || s.toLowerCase() === "null" || s.toLowerCase() === "none") return "OTHER";
  return String(s).toUpperCase();
}

function txnChecksum(txns) {
  if (!Array.isArray(txns)) return "";
  const len = txns.length;
  const last = txns.length ? txns[txns.length - 1].txn_datetime || txns[txns.length - 1].sms_timestamp || "" : "";
  let sum = 0;
  for (let i = Math.max(0, txns.length - 50); i < txns.length; i++) {
    const a = Number(txns[i].amount || 0);
    sum += (isNaN(a) ? 0 : Math.round(a));
  }
  return `${len}|${last}|${sum}`;
}

function getRangeDates(kind, customFrom, customTo) {
  const now = new Date();
  switch (kind) {
    case "TODAY": return [startOfDay(now), endOfDay(now)];
    case "7D": { const s = new Date(); s.setDate(now.getDate() - 6); return [startOfDay(s), endOfDay(now)]; }
    case "30D": { const s = new Date(); s.setDate(now.getDate() - 29); return [startOfDay(s), endOfDay(now)]; }
    case "THIS_MONTH": return [startOfDay(new Date(now.getFullYear(), now.getMonth(), 1)), endOfDay(now)];
    case "LAST_MONTH": { const s = new Date(now.getFullYear(), now.getMonth() - 1, 1); const e = new Date(now.getFullYear(), now.getMonth(), 0); return [startOfDay(s), endOfDay(e)]; }
    case "CUSTOM": if (customFrom && customTo) return [startOfDay(new Date(customFrom)), endOfDay(new Date(customTo))]; return [null, null];
    case "OVERALL": return [null, null];
    default: return [null, null];
  }
}

/* ---------- computeAggregates stays SAME ---------- */
function computeAggregates(transactions) {
  const modeMap = {};
  const monthlyMap = {};
  const dailyMonthMap = {};
  const topDebits = [];
  const yearsSet = new Set();
  const txnsByMonthYear = {};

  for (let i = 0; i < transactions.length; i++) {
    const t = transactions[i];
    if (!t) continue;

    const dt = t.txn_datetime ? new Date(t.txn_datetime) : (t.sms_timestamp ? new Date(t.sms_timestamp) : null);
    if (!dt || isNaN(dt.getTime())) {
      if ((t.type || "").toLowerCase() === "debit")
        topDebits.push({ ...t, amountNum: Number(t.amount || 0) });
      continue;
    }

    const year = dt.getFullYear();
    const month = dt.getMonth() + 1;
    yearsSet.add(year);
    const monthKey = `${year}-${String(month).padStart(2, "0")}`;

    if (!monthlyMap[monthKey]) monthlyMap[monthKey] = { credit: 0, debit: 0 };
    if ((t.type || "").toLowerCase() === "credit") monthlyMap[monthKey].credit += Number(t.amount || 0);
    else if ((t.type || "").toLowerCase() === "debit") monthlyMap[monthKey].debit += Number(t.amount || 0);

    if (!txnsByMonthYear[monthKey]) txnsByMonthYear[monthKey] = [];
    txnsByMonthYear[monthKey].push(t);

    if ((t.type || "").toLowerCase() === "debit") {
      const m = normalizeMode(t.mode);
      if (m !== "AUTO") modeMap[m] = (modeMap[m] || 0) + Number(t.amount || 0);
      topDebits.push({ ...t, amountNum: Number(t.amount || 0) });
    }
  }

  const topDebitsFiltered = topDebits
    .filter(t => (t.type || "").toLowerCase() === "debit" && normalizeMode(t.mode) !== "AUTO")
    .sort((a, b) => b.amountNum - a.amountNum);

  const modeEntries = Object.entries(modeMap).map(([k, v]) => ({ mode: k, value: Math.round(v * 100) / 100 }))
    .sort((a, b) => b.value - a.value);

  const incExpArray = Object.entries(monthlyMap).map(([k, v]) => ({
    month: k,
    credit: Math.round(v.credit * 100) / 100,
    debit: Math.round(v.debit * 100) / 100
  })).sort((a, b) => a.month.localeCompare(b.month));

  return {
    modeEntries,
    incExpArray,
    topDebitsFiltered,
    txnsByMonthYear,
    years: Array.from(yearsSet).sort((a, b) => b - a)
  };
}

/* ---------- COMPONENT ---------- */
export default function Chart() {
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);

  const [loading, setLoading] = useState(false);
  const [globalRangeKind, setGlobalRangeKind] = useState("30D");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");

  const today = new Date();
  const [selectedMonthIdx, setSelectedMonthIdx] = useState(today.getMonth());
  const [selectedYear, setSelectedYear] = useState(today.getFullYear());
  const [topN, setTopN] = useState(5);

  const [selectedAccount, setSelectedAccount] = useState(() => localStorage.getItem("selectedAccountFilter") || "ALL");

  const [expandedChart, setExpandedChart] = useState(null);
  const [detailRows, setDetailRows] = useState([]);
  const [modalRenderKey, setModalRenderKey] = useState(0);

  const [aggregates, setAggregates] = useState({
    modeEntries: [],
    incExpArray: [],
    topDebitsFiltered: [],
    txnsByMonthYear: {},
    years: []
  });

  const COLORS = ["#1a73e8", "#34a853", "#fbbc04", "#ea4335", "#8e44ad", "#0f766e", "#7c3aed"];

  const checksumRef = useRef("");
  const computingRef = useRef(false);

  /* ----------------------------------
       🔥 RELOAD FIX (ONLY NEW PART)
  ---------------------------------- */

  // throttle reloads to once every 2 sec
  const reloadTimer = useRef(null);

  function scheduleReload() {
    if (reloadTimer.current) return; // already scheduled
    reloadTimer.current = setTimeout(() => {
      loadAll();
      reloadTimer.current = null; // allow next reload
    }, 2000);
  }

  /* ---------- Instant load from localStorage ---------- */
  useEffect(() => {
    try {
      const acc = JSON.parse(localStorage.getItem("accounts"));
      const tx = JSON.parse(localStorage.getItem("transactions_all"));
      const agg = JSON.parse(localStorage.getItem("chart_aggregates"));

      if (Array.isArray(acc)) {
        setAccounts(acc.map(a => ({
          id: a.id,
          number: String(a.number || a.account_number || ""),
          acronym: a.acronym || a.bank?.slice(0,3)?.toUpperCase() || "",
          bank: a.bank || a.bank_name || "",
          balance: Number(a.balance || a.current_balance || 0)
        })));
      }
      if (Array.isArray(tx)) setTransactions(tx);

      if (agg && agg._checksum === (tx ? txnChecksum(tx) : "")) {
        setAggregates(agg.data || aggregates);
        checksumRef.current = agg._checksum;
      }
    } catch {}

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------- Load fresh from backend ---------- */
  async function loadAll() {
    setLoading(true);
    try {
      const [accRaw, txRaw] = await Promise.all([
        listAccounts(),
        fetchTransactions("ALL")
      ]);

      const accConverted = (accRaw || []).map(a => ({
        id: a.id,
        number: String(a.account_number),
        acronym: a.acronym,
        bank: a.bank_name,
        balance: Number(a.current_balance || 0)
      }));

      const txConverted = Array.isArray(txRaw) ? txRaw : [];

      setAccounts(accConverted);
      setTransactions(txConverted);

      localStorage.setItem("accounts", JSON.stringify(accConverted));
      localStorage.setItem("transactions_all", JSON.stringify(txConverted));

      scheduleComputeAggregates(txConverted);

    } catch (e) {
      console.error("Chart load failed", e);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- Mount + Event listeners (with throttling) ---------- */
  useEffect(() => {
    loadAll();

    const handleAccountFilter = (e) => {
      const v = String(e.detail || "ALL");
      setSelectedAccount(v);
      localStorage.setItem("selectedAccountFilter", v);
    };

    window.addEventListener("accountsUpdated", scheduleReload);
    window.addEventListener("transactionsUpdated", scheduleReload);
    window.addEventListener("accountFilterChanged", handleAccountFilter);

    return () => {
      window.removeEventListener("accountsUpdated", scheduleReload);
      window.removeEventListener("transactionsUpdated", scheduleReload);
      window.removeEventListener("accountFilterChanged", handleAccountFilter);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------- Aggregates (unchanged) ---------- */
  function scheduleComputeAggregates(txns) {
    const cs = txnChecksum(txns || transactions);
    if (cs === checksumRef.current) return;
    checksumRef.current = cs;

    if (computingRef.current) {
      setTimeout(() => scheduleComputeAggregates(txns), 120);
      return;
    }

    computingRef.current = true;
    setTimeout(() => {
      try {
        const agg = computeAggregates(txns || transactions);
        setAggregates(agg);
        localStorage.setItem("chart_aggregates", JSON.stringify({ _checksum: cs, data: agg }));
      } finally {
        computingRef.current = false;
      }
    }, 30);
  }

  useEffect(() => {
    scheduleComputeAggregates(transactions);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transactions]);

  /* ---------------- Range filtering etc — UNCHANGED ---------------- */
  const [globalStart, globalEnd] = useMemo(
    () => getRangeDates(globalRangeKind, customFrom, customTo),
    [globalRangeKind, customFrom, customTo]
  );

  const txnsInRange = useMemo(() => {
    if (!transactions.length) return [];
    if (!globalStart || !globalEnd) return transactions;
    return transactions.filter(t => {
      const dt = t.txn_datetime ? new Date(t.txn_datetime)
        : (t.sms_timestamp ? new Date(t.sms_timestamp) : null);
      if (!dt || isNaN(dt.getTime())) return false;
      return dt >= globalStart && dt <= globalEnd;
    });
  }, [transactions, globalStart, globalEnd]);

  const filteredByAccount = useMemo(() => {
    if (!txnsInRange.length) return [];
    if (selectedAccount === "ALL") return txnsInRange;

    return txnsInRange.filter(t => {
      const candidates = [
        t.account_number, t.account_number?.toString?.(),
        t.account_id, t.account_id?.toString?.(),
        t.sms_account_number, t.sms_account_number?.toString?.(),
        t.sms_account, t.sms_account?.toString?.()
      ];
      return candidates.some(x => x != null && String(x) === String(selectedAccount));
    });
  }, [txnsInRange, selectedAccount]);

  /* ----------------- All charts below REMAIN EXACTLY SAME ----------------- */
  /*  (NO LOGIC CHANGES, ONLY RELOAD FIX WAS ADDED AT THE TOP)               */

  const pieData = useMemo(() => {
    return (accounts || []).map(a => ({ name: a.acronym || a.number, value: Number(a.balance || 0) }));
  }, [accounts]);

  const totalBalance = useMemo(() => pieData.reduce((s, x) => s + Number(x.value || 0), 0), [pieData]);

  const modeData = useMemo(() => {
    const map = {};
    for (let i = 0; i < filteredByAccount.length; i++) {
      const t = filteredByAccount[i];
      if (!t) continue;
      if ((t.type || "").toLowerCase() !== "debit") continue;
      const m = normalizeMode(t.mode);
      if (m === "AUTO") continue;
      map[m] = (map[m] || 0) + Number(t.amount || 0);
    }
    return Object.entries(map).map(([k, v]) => ({ type: k, value: Math.round(v * 100) / 100 }))
      .sort((a, b) => b.value - a.value);
  }, [filteredByAccount]);

  const totalModeValue = useMemo(() => modeData.reduce((s, x) => s + Number(x.value || 0), 0), [modeData]);

  const monthlyDaily = useMemo(() => {
    const y = Number(selectedYear);
    const m = Number(selectedMonthIdx);
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    const arr = Array.from({ length: daysInMonth }, (_, i) => ({ day: i + 1, value: 0 }));

    for (let i = 0; i < filteredByAccount.length; i++) {
      const t = filteredByAccount[i];
      if (!t) continue;
      if ((t.type || "").toLowerCase() !== "debit") continue;
      const mode = normalizeMode(t.mode);
      if (mode === "AUTO") continue;
      const dt = t.txn_datetime ? new Date(t.txn_datetime) : (t.sms_timestamp ? new Date(t.sms_timestamp) : null);
      if (!dt || isNaN(dt.getTime())) continue;
      if (dt.getFullYear() === y && dt.getMonth() === m) {
        const d = dt.getDate();
        arr[d - 1].value += Number(t.amount || 0);
      }
    }
    return arr.map(r => ({ ...r, value: Math.round(r.value * 100) / 100 }));
  }, [filteredByAccount, selectedMonthIdx, selectedYear]);

  const incExp = useMemo(() => {
    const map = {};
    for (let i = 0; i < filteredByAccount.length; i++) {
      const t = filteredByAccount[i];
      if (!t) continue;
      const dt = t.txn_datetime ? new Date(t.txn_datetime)
        : (t.sms_timestamp ? new Date(t.sms_timestamp) : null);
      if (!dt || isNaN(dt.getTime())) continue;
      const key = `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}`;
      if (!map[key]) map[key] = { month: key, credit: 0, debit: 0 };
      if ((t.type || "").toLowerCase() === "credit") map[key].credit += Number(t.amount || 0);
      if ((t.type || "").toLowerCase() === "debit" && normalizeMode(t.mode) !== "AUTO")
        map[key].debit += Number(t.amount || 0);
    }
    return Object.values(map).sort((a, b) => a.month.localeCompare(b.month))
      .map(r => ({ ...r, credit: Math.round(r.credit * 100) / 100, debit: Math.round(r.debit * 100) / 100 }));
  }, [filteredByAccount]);

  const topDebits = useMemo(() => {
    const list = [];
    for (let i = 0; i < filteredByAccount.length; i++) {
      const t = filteredByAccount[i];
      if (!t) continue;
      if ((t.type || "").toLowerCase() !== "debit") continue;
      if (normalizeMode(t.mode) === "AUTO") continue;
      list.push({ ...t, amountNum: Number(t.amount || 0) });
    }
    list.sort((a, b) => b.amountNum - a.amountNum);
    return list.slice(0, Number(topN || 5));
  }, [filteredByAccount, topN]);

  const availableYears = useMemo(() => {
    if (aggregates.years.length) return aggregates.years;
    const s = new Set();
    for (let i = 0; i < transactions.length; i++) {
      const t = transactions[i];
      const dt = t.txn_datetime ? new Date(t.txn_datetime)
        : (t.sms_timestamp ? new Date(t.sms_timestamp) : null);
      if (dt && !isNaN(dt.getTime())) s.add(dt.getFullYear());
    }
    const arr = [...s].sort((a, b) => b - a);
    if (!arr.includes(new Date().getFullYear())) arr.unshift(new Date().getFullYear());
    return arr;
  }, [aggregates, transactions]);

  function openModal(key) {
    let rows = [];
    if (key === "spendingPie") {
      rows = modeData.map(m => ({ label: m.type, amount: m.value, percent: totalModeValue ? ((m.value / totalModeValue) * 100).toFixed(1) : "0.0" }));
    } else if (key === "monthlyHistogram") {
      rows = monthlyDaily.map(d => ({ day: d.day, amount: d.value }));
    } else if (key === "incomeVsExpense") {
      rows = incExp.map(r => ({ month: r.month, credit: r.credit, debit: r.debit }));
    } else if (key === "topDebits") {
      rows = topDebits.map(t => ({ id: t.id, date: t.txn_datetime || t.sms_timestamp, amount: Number(t.amount || 0), desc: t.description || t.reference_id || "-" }));
    } else if (key === "balancePie") {
      rows = pieData.map(p => ({ value: p.value, percent: totalBalance ? ((p.value / totalBalance) * 100).toFixed(1) : "0.0" }));
    }
    setDetailRows(rows);
    setExpandedChart(key);
    setTimeout(() => setModalRenderKey(k => k + 1), 60);
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    setExpandedChart(null);
    setDetailRows([]);
    document.body.style.overflow = "";
  }

  function renderModalTable() {
    if (!detailRows.length) return <div className={style.noData}>No details</div>;
    return (
      <table className={style.detailTable}>
        <thead>
          {expandedChart === "spendingPie" && <tr><th>Mode</th><th>Amount</th><th>%</th></tr>}
          {expandedChart === "monthlyHistogram" && <tr><th>Day</th><th>Amount</th></tr>}
          {expandedChart === "incomeVsExpense" && <tr><th>Month</th><th>Credit</th><th>Debit</th></tr>}
          {expandedChart === "topDebits" && <tr><th>ID</th><th>Date</th><th>Amount</th><th>Description</th></tr>}
          {expandedChart === "balancePie" && <tr><th>Amount</th><th>%</th></tr>}
        </thead>
        <tbody>
          {detailRows.map((r, i) => (
            expandedChart === "spendingPie" ? <tr key={i}><td>{r.label}</td><td>{rupee(r.amount)}</td><td>{r.percent}%</td></tr> :
            expandedChart === "monthlyHistogram" ? <tr key={i}><td>{r.day}</td><td>{rupee(r.amount)}</td></tr> :
            expandedChart === "incomeVsExpense" ? <tr key={i}><td>{r.month}</td><td>{rupee(r.credit)}</td><td>{rupee(r.debit)}</td></tr> :
            expandedChart === "topDebits" ? <tr key={i}><td>{r.id}</td><td>{r.date ? new Date(r.date).toLocaleString() : "-"}</td><td>{rupee(r.amount)}</td><td>{r.desc}</td></tr> :
            expandedChart === "balancePie" ? <tr key={i}><td>{rupee(r.value)}</td><td>{r.percent}%</td></tr> :
            null
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <div className={style.main}>
      <div className={style.controlsRow}>
        <div />
        <div className={style.rightControls}>
          <label className={style.label}>Range</label>
          <select className={style.select} value={globalRangeKind} onChange={(e) => setGlobalRangeKind(e.target.value)}>
            <option value="TODAY">Today</option>
            <option value="7D">Last 7 Days</option>
            <option value="30D">Last 30 Days</option>
            <option value="THIS_MONTH">This Month</option>
            <option value="LAST_MONTH">Last Month</option>
            <option value="CUSTOM">Custom</option>
            <option value="OVERALL">OVERALL (Ignore Range)</option>
          </select>

          {globalRangeKind === "CUSTOM" && (
            <div className={style.customRange}>
              <input type="date" value={customFrom} onChange={(e) => setCustomFrom(e.target.value)} />
              <span className={style.rangeSep}>—</span>
              <input type="date" value={customTo} onChange={(e) => setCustomTo(e.target.value)} />
            </div>
          )}
        </div>
      </div>

      <h2 className={style.heading}>Analytics</h2>

      <div className={style.balanceBox}>
        <div>
          <h3 className={style.balanceTitle}>
            Available Balance {selectedAccount === "ALL" ? "(All Accounts)" : ""}
          </h3>
          <div className={style.balanceAmount}>
            {selectedAccount === "ALL"
              ? rupee(totalBalance)
              : rupee((accounts.find(a => a.number === selectedAccount)?.balance) || 0)
            }
          </div>
        </div>
        <div style={{ textAlign: "right", color: "#666", fontSize: 12 }}>
          Showing transactions in selected range
        </div>
      </div>

      <div className={style.gridContainer}>
        {selectedAccount === "ALL" && (
          <div className={style.card}>
            <div className={style.cardHeader}>
              <h3 className={style.chartHeading}>Balance Distribution</h3>
              <div className={style.cardFilters}>
                <button className={style.smallBtn} onClick={() => openModal("balancePie")}>View Details</button>
              </div>
            </div>
            <div className={style.chartBox}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pieData} dataKey="value" outerRadius={90}
                    label={({ payload }) => `${rupee(payload.value)} (${totalBalance ? ((payload.value / totalBalance) * 100).toFixed(1) : "0.0"}%)`}
                    labelLine={false}
                  >
                    {pieData.map((entry, idx) => <Cell key={idx} fill={COLORS[idx % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => rupee(v)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className={style.card}>
          <div className={style.cardHeader}>
            <h3 className={style.chartHeading}>Spending Mode</h3>
            <div className={style.cardFilters}>
              <button className={style.smallBtn} onClick={() => openModal("spendingPie")}>View Details</button>
            </div>
          </div>
          <div className={style.chartBox}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={modeData} dataKey="value" nameKey="type" outerRadius={80}
                  label={({ payload, percent }) => `${rupee(payload.value)} (${(percent * 100).toFixed(1)}%)`}
                  labelLine={false}
                >
                  {modeData.map((entry, idx) => <Cell key={idx} fill={COLORS[idx % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(val) => rupee(val)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={style.card}>
          <div className={style.cardHeader}>
            <h3 className={style.chartHeading}>Monthly Spend (Daily)</h3>
            <div className={style.cardFilters}>
              <select className={style.smallSelect} value={selectedMonthIdx} onChange={(e) => setSelectedMonthIdx(Number(e.target.value))}>
                {MONTHS.map(m => <option key={m.idx} value={m.idx}>{m.label}</option>)}
              </select>

              <select className={style.smallSelect} value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
                {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
              </select>

              <button className={style.smallBtn} onClick={() => openModal("monthlyHistogram")}>View Details</button>
            </div>
          </div>
          <div className={style.chartBox}>
            <ResponsiveContainer>
              <BarChart data={monthlyDaily}>
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip formatter={v => rupee(v)} />
                <Bar dataKey="value" fill="#1a73e8" barSize={26} radius={[6, 6, 6, 6]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={style.card}>
          <div className={style.cardHeader}>
            <h3 className={style.chartHeading}>Income vs Expense</h3>
            <div className={style.cardFilters}>
              <button className={style.smallBtn} onClick={() => openModal("incomeVsExpense")}>View Details</button>
            </div>
          </div>
          <div className={style.chartBox}>
            <ResponsiveContainer>
              <BarChart data={incExp}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={v => rupee(v)} />
                <Legend />
                <Bar dataKey="credit" fill="#34a853" />
                <Bar dataKey="debit" fill="#ea4335" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={style.card}>
          <div className={style.cardHeader}>
            <h3 className={style.chartHeading}>Top Expenses</h3>
            <div className={style.cardFilters}>
              <select className={style.smallSelect} value={topN} onChange={(e) => setTopN(Number(e.target.value))}>
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
              </select>
              <button className={style.smallBtn} onClick={() => openModal("topDebits")}>View Details</button>
            </div>
          </div>
          <div className={style.chartBox}>
            <ResponsiveContainer>
              <BarChart layout="vertical" data={topDebits.map(t => ({ name: (`Ref:${t.reference_id || t.id}`), value: Number(t.amount || 0) }))}>
                <XAxis type="number" />
                <YAxis type="category" dataKey="name" width={150} />
                <Tooltip formatter={v => rupee(v)} />
                <Bar dataKey="value" fill="#ea4335" barSize={12} radius={[6, 6, 6, 6]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {expandedChart && (
        <div className={style.modalOverlay} onClick={closeModal}>
          <div className={style.modalCard} onClick={(e) => e.stopPropagation()}>
            <button className={style.modalCloseBtn} onClick={closeModal}>✕</button>
            <h2 className={style.modalTitle}>
              {expandedChart === "balancePie" && "Balance Distribution"}
              {expandedChart === "spendingPie" && "Spending Mode Breakdown"}
              {expandedChart === "monthlyHistogram" && `Daily Spend — ${MONTHS[selectedMonthIdx].label} ${selectedYear}`}
              {expandedChart === "incomeVsExpense" && "Income vs Expense"}
              {expandedChart === "topDebits" && `Top ${topN} Expenses`}
            </h2>

            <div className={style.modalChartBox} key={modalRenderKey}>
              <ResponsiveContainer width="100%" height="100%">
                {expandedChart === "balancePie" && (
                  <PieChart>
                    <Pie data={pieData} dataKey="value" outerRadius={140}
                      label={({ payload }) => `${rupee(payload.value)} (${totalBalance ? ((payload.value / totalBalance) * 100).toFixed(1) : "0.0"}%)`}
                      labelLine={false}
                    >
                      {pieData.map((e, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={v => rupee(v)} />
                  </PieChart>
                )}

                {expandedChart === "spendingPie" && (
                  <PieChart>
                    <Pie data={modeData} dataKey="value" nameKey="type" outerRadius={140}
                      label={({ payload, percent }) => `${rupee(payload.value)} (${(percent * 100).toFixed(1)}%)`}
                      labelLine={false}
                    >
                      {modeData.map((e, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={v => rupee(v)} />
                    <Legend />
                  </PieChart>
                )}

                {expandedChart === "monthlyHistogram" && (
                  <BarChart data={monthlyDaily}>
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip formatter={v => rupee(v)} />
                    <Bar dataKey="value" fill="#1a73e8" barSize={28} radius={[6, 6, 6, 6]} />
                  </BarChart>
                )}

                {expandedChart === "incomeVsExpense" && (
                  <BarChart data={incExp}>
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={v => rupee(v)} />
                    <Legend />
                    <Bar dataKey="credit" fill="#34a853" />
                    <Bar dataKey="debit" fill="#ea4335" />
                  </BarChart>
                )}

                {expandedChart === "topDebits" && (
                  <BarChart layout="vertical" data={topDebits.map(t => ({ ...t, name: (t.description || t.reference_id || t.id).slice(0, 60) }))}>
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={300} />
                    <Tooltip formatter={v => rupee(v)} />
                    <Bar dataKey="amount" fill="#ea4335" barSize={14} />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>

            <div className={style.modalTableBox}>
              <h3>Details</h3>
              {renderModalTable()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
