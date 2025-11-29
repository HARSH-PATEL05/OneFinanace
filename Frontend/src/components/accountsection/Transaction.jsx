// Transaction.jsx
import { useEffect, useState, useRef } from "react";
import style from "./Style/Transaction.module.css";
import {
    fetchTransactions,
    deleteAllTransactions,
    deleteTransactionsForAccount,
} from "@/Api"; // adjust path if your Api.js import path differs

export default function Transaction() {
    const [transactions, setTransactions] = useState([]);
    const [selected, setSelected] = useState("ALL");

    const [query, setQuery] = useState("");
    const [sortBy, setSortBy] = useState("latest");
    const [visibleCount, setVisibleCount] = useState(10);

    const [modalTxn, setModalTxn] = useState(null);
    const [showDownloadModal, setShowDownloadModal] = useState(false);

    // DATE FILTER states
    const [showDateModal, setShowDateModal] = useState(false);
    // active applied filter
    const [dateFilter, setDateFilter] = useState({ type: "none", from: null, to: null });
    // temporary editing filter inside modal
    const [tempDateFilter, setTempDateFilter] = useState({ type: "none", from: null, to: null });

    const [loading, setLoading] = useState(false);
    const listRef = useRef(null);

    /* ----------------- load transactions from backend ----------------- */

    // helper to actually fetch (all or by account)
    const loadTransactions = async (accountNumber = "ALL") => {
        setLoading(true);
        try {
            const data = await fetchTransactions(accountNumber);
            // backend returns objects with fields like account_id, sms_account_number, txn_datetime, etc.
            // keep as-is — UI uses txn_datetime, bank, etc. If backend uses account_id instead of bank,
            // ensure your backend returns 'bank' or frontend adapts. For now we accept backend fields.
            setTransactions(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error("Failed to load transactions", err);
            setTransactions([]);
        } finally {
            setLoading(false);
            window.dispatchEvent(new Event("transactionsUpdated"));

        }
    };

    // initial load — read selectedAccountFilter (account_number) from localStorage
    useEffect(() => {
        const saved = localStorage.getItem("selectedAccountFilter") || "ALL";
        setSelected(saved);
        loadTransactions(saved);
    }, []);

    // listen for account filter changes broadcasted by Bankaccount component
    useEffect(() => {
        const handler = (e) => {
            const acc = String(e.detail || "ALL");
            setSelected(acc);
            setVisibleCount(10);
            // fetch transactions for new account
            loadTransactions(acc);
        };
        window.addEventListener("accountFilterChanged", handler);
        return () => window.removeEventListener("accountFilterChanged", handler);
    }, []);

    /* ---------------- FILTER + SEARCH + SORT + DATE ---------------- */

    const filterBySelected = (txns) =>
        selected === "ALL" ? txns : txns.filter((t) => {
            // Some backends may return 'account_id' (preferred) — allow matching either account_id or bank
            const accountId = t.account_id ?? t.accountId ?? t.sms_account_number ?? "";
            // selected is expected to be account_number per Option A
            return String(accountId) === String(selected);
        });

    const searchFilter = (txns) => {
        const q = query.trim().toLowerCase();
        if (!q) return txns;

        return txns.filter((t) =>
            [
                t.bankName, // if backend returns bank
                t.type,
                t.description,
                t.mode,
                t.reference_id,
                t.sms_account_number,
                t.sms_formatted_datetime,
            ]
                .filter(Boolean)
                .some((x) => x.toLowerCase().includes(q))
        );
    };

    // helper: convert a Date-like to yyyy-mm-dd local string
    function toYMDLocal(dateObj) {
        if (!dateObj) return null;
        const d = new Date(dateObj);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    }

    const applyDateFilterToList = (txns) => {
        const df = dateFilter;
        if (!df || df.type === "none") return txns;

        const within = (txnDateStr) => {
            const d = new Date(txnDateStr);
            if (Number.isNaN(d.getTime())) return false;
            const ymd = toYMDLocal(d);
            if (df.type === "today") {
                const today = toYMDLocal(new Date());
                return ymd === today;
            }
            if (df.type === "yesterday") {
                const t = new Date();
                t.setDate(t.getDate() - 1);
                return ymd === toYMDLocal(t);
            }
            if (df.type === "custom") {
                if (!df.from || !df.to) return true;
                return ymd >= df.from && ymd <= df.to;
            }
            return true;
        };

        return txns.filter((t) => within(t.txn_datetime));
    };

    const sortTxns = (txns) => {
        const c = [...txns];
        switch (sortBy) {
            case "latest":
                c.sort((a, b) => new Date(b.txn_datetime) - new Date(a.txn_datetime));
                break;
            case "oldest":
                c.sort((a, b) => new Date(a.txn_datetime) - new Date(b.txn_datetime));
                break;
            case "amountAsc":
                c.sort((a, b) => Number(a.amount) - Number(b.amount));
                break;
            case "amountDesc":
                c.sort((a, b) => Number(b.amount) - Number(a.amount));
                break;
            default:
                break;
        }
        return c;
    };

    // processed list = selected filter -> date filter -> search -> sort
    const processed = sortTxns(
        searchFilter(applyDateFilterToList(filterBySelected(transactions)))
    );
    const visible = processed.slice(0, visibleCount);

    /*Helper function for date time conversion  */
    function formatTimestamp(ts) {
        if (!ts) return "";

        // If backend gives ISO with microseconds → remove after "."
        const clean = ts.split(".")[0];  // "2025-11-21T08:30:27"

        // Convert T → space
        return clean.replace("T", " ");
    }

    /* ---------------- LOAD MORE ON SCROLL ---------------- */

    const onScroll = (e) => {
        const el = e.target;
        if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) {
            setVisibleCount((v) => Math.min(processed.length, v + 8));
        }
    };

    const formatSigned = (type, amt) =>
        (String(type).toUpperCase() === "CREDIT" ? "+" : "-") + Number(amt).toLocaleString();


    /* ---------------- MODAL ---------------- */

    const openModal = (t) => {
        setModalTxn(t);
        document.body.style.overflow = "hidden";
    };

    const closeModal = () => {
        setModalTxn(null);
        document.body.style.overflow = "";
    };

    /* ---------------- CLEAR ALL (bank-wise / account-wise) ---------------- */

    const clearAll = async () => {
        const msg =
            selected === "ALL" ? "Are you sure? Delete ALL transactions?" : `Delete ALL transactions of ${selected}?`;

        if (!confirm(msg)) return;

        try {
            if (selected === "ALL") {
                await deleteAllTransactions();
            } else {
                // selected is expected to be account_number (Option A)
                await deleteTransactionsForAccount(selected);
            }
            // reload after delete
            await loadTransactions(selected);
        } catch (err) {
            console.error("Clear failed", err);
            alert("Failed to delete transactions. See console.");
        }
    };

    /* ---------------- DOWNLOAD (unchanged) ---------------- */

    const downloadData = async (format) => {
        const rows = processed;
        if (!rows.length) return alert("No transactions");

        if (format === "csv") {
            const header = Object.keys(rows[0]).join(",");
            const lines = rows.map((r) =>
                Object.values(r)
                    .map((v) => `"${String(v).replace(/"/g, '""')}"`)
                    .join(",")
            );
            const blob = new Blob([header + "\n" + lines.join("\n")], {
                type: "text/csv",
            });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "transactions.csv";
            a.click();
        }

        if (format === "txt") {
            const lines = rows.map(
                (r) =>
                    `ID:${r.id} | ${r.bankName} | ${r.type} | ${formatSigned(r.type, r.amount)} | Balance:₹${r.balance_after_txn}`
            );
            const blob = new Blob([lines.join("\n")], { type: "text/plain" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "transactions.txt";
            a.click();
        }

        if (format === "excel") {
            try {
                const XLSX = await import("xlsx");
                const sheet = XLSX.utils.json_to_sheet(rows);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, sheet, "Transactions");
                XLSX.writeFile(wb, "transactions.xlsx");
            } catch (err) {
                alert("xlsx not found. Install: npm install xlsx");
            }
        }

        if (format === "pdf") {
            let html = `
<html><head><title>Transactions</title>
<style>
body{font-family:Arial;padding:20px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid #ccc;padding:8px;text-align:left}th{background:#f3f4f6;font-weight:700}
</style></head><body><h2>Transactions</h2><table><thead><tr><th>ID</th><th>Bank</th><th>Type</th><th>Amount</th><th>Balance</th><th>Date</th><th>Description</th></tr></thead><tbody>
`;
            rows.forEach((r) => {
                html += `<tr><td>${r.id}</td><td>${r.bankName}</td><td>${r.type}</td><td>${formatSigned(r.type, r.amount)}</td><td>₹${r.balance_after_txn.toLocaleString()}</td><td>${r.txn_datetime}</td><td>${r.description}</td></tr>`;
            });
            html += `</tbody></table></body></html>`;
            const win = window.open("", "_blank");
            win.document.write(html);
            win.document.close();
            win.print();
        }

        setShowDownloadModal(false);
    };

    /* ---------------- DATE MODAL HANDLERS ---------------- */

    const openDateModal = () => {
        setTempDateFilter({ ...dateFilter });
        setShowDateModal(true);
    };

    const applyDateModal = () => {
        setDateFilter({ ...tempDateFilter });
        setShowDateModal(false);
    };

    const cancelDateModal = () => {
        setTempDateFilter({ ...dateFilter });
        setShowDateModal(false);
    };

    const setTempFrom = (val) => setTempDateFilter((p) => ({ ...p, from: val }));
    const setTempTo = (val) => setTempDateFilter((p) => ({ ...p, to: val }));

    const pickToday = () => setTempDateFilter({ type: "today", from: null, to: null });
    const pickYesterday = () => setTempDateFilter({ type: "yesterday", from: null, to: null });
    const pickCustom = () => setTempDateFilter((p) => ({ ...p, type: "custom" }));

    /* ---------------- RENDER (UI preserved) ---------------- */

    return (
        <div className={style.container}>
            {/* HEADER */}
            <div className={style.headerRow}>
                <div className={style.titleBlock}>Transactions</div>

                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <button className={style.clearAllBtn} onClick={clearAll}>
                        Clear All
                    </button>
                </div>

                <button className={style.downloadBtn} onClick={() => setShowDownloadModal(true)}>
                    Download ▼
                </button>
            </div>

            {/* FILTER ROW 1 (Sort + Date) */}
            <div className={style.filterRow1}>
                <select
                    className={style.sortSmall}
                    value={sortBy}
                    onChange={(e) => {
                        setSortBy(e.target.value);
                        setVisibleCount(10);
                    }}
                >
                    <option value="latest">Latest</option>
                    <option value="oldest">Oldest</option>
                    <option value="amountDesc">High → Low</option>
                    <option value="amountAsc">Low → High</option>
                </select>

                <button className={style.dateBtn} onClick={openDateModal}>
                    📅
                </button>
                <button
                    className={style.clearFilterBtn}
                    onClick={() => {
                        setQuery("");
                        setSortBy("latest");
                        setDateFilter({ type: "none", from: null, to: null });
                        setVisibleCount(10);
                    }}
                >
                    Clear Filter
                </button>
            </div>

            {/* FILTER ROW 2 (Full Search bar) */}
            <div className={style.filterRow2}>
                <input
                    className={style.searchFull}
                    placeholder="Search..."
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        setVisibleCount(10);
                    }}
                />
            </div>

            {/* LIST */}
            <div className={style.list} onScroll={onScroll} ref={listRef}>
                {loading ? (
                    <div style={{ padding: 20, textAlign: "center", color: "#6b7280" }}>Loading...</div>
                ) : visible.length === 0 ? (
                    <div style={{ padding: 20, textAlign: "center", color: "#6b7280" }}>No transactions</div>
                ) : (
                    visible.map((t) => (
                        <div key={t.id} className={style.cardWrapper}>
                            <div className={style.card} onClick={() => openModal(t)}>
                                <div className={style.grid}>
                                    <div className={style.bankName} style={{ gridColumn: "1 / span 2" }}>
                                        {t.bankName.toUpperCase() ?? t.account_id ?? t.sms_account_number ?? "—"}
                                    </div>

                                    <div
                                        className={
                                            String(t.type).toUpperCase() === "CREDIT"
                                                ? `${style.colRight} ${style.creditText}`
                                                : `${style.colRight} ${style.debitText}`
                                        }
                                    >
                                        {t.type.toUpperCase()}
                                    </div>


                                    <div className={style.details} style={{ gridColumn: "1 / span 2" }}>
                                        {t.mode} / {t.account_id} / {t.reference_id}
                                    </div>

                                    <div className={`${style.colRight} ${style.amount}`}>
                                        <div className={String(t.type).toUpperCase() === "CREDIT" ? style.creditAmount : style.debitAmount}>
                                            {formatSigned(t.type, t.amount)}
                                        </div>
                                    </div>

                                    <div className={style.details} style={{ gridColumn: "1 / span 2" }}>
                                        {t.sms_formatted_datetime || formatTimestamp(t.txn_datetime)}

                                    </div>

                                    <div className={`${style.colRight} ${style.balance}`}>Rs {t.balance_after_txn?.toLocaleString?.()}</div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* FULL MODAL */}
            {modalTxn && (
                <div className={style.modalOverlay} onClick={closeModal}>
                    <div className={style.modalBox} onClick={(e) => e.stopPropagation()}>
                        <button className={style.modalClose} onClick={closeModal}>✕</button>

                        <h3 className={style.modalTitle}>
                            {modalTxn.bankName ?? modalTxn.account_id} — {modalTxn.type}
                        </h3>

                        <div className={style.modalContent}>
                            <div className={style.modalRow}>
                                <strong>Amount:</strong> {formatSigned(modalTxn.type, modalTxn.amount)}
                            </div>

                            <div className={style.modalRow}>
                                <strong>Balance After:</strong> ₹ {modalTxn.balance_after_txn?.toLocaleString?.()}
                            </div>

                            <div className={style.modalRow}>
                                <strong>When:</strong> {modalTxn.sms_formatted_datetime}
                            </div>

                            <div className={style.modalRow}>
                                <strong>Description:</strong> {modalTxn.description}
                            </div>

                            <div className={style.modalRow}>
                                <strong>Mode:</strong> {modalTxn.mode}
                            </div>

                            <div className={style.modalRow}>
                                <strong>Account:</strong> {modalTxn.sms_account_number ?? modalTxn.account_id}
                            </div>

                            <div className={style.modalRow}>
                                <strong>Reference:</strong> {modalTxn.reference_id}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* DATE FILTER MODAL */}
            {showDateModal && (
                <>
                    <div className={style.sectionOverlay} onClick={cancelDateModal}></div>

                    <div className={style.dateModal}>
                        <button className={style.centerClose} onClick={cancelDateModal}>
                            ✕
                        </button>

                        <div className={style.dateOption} onClick={() => { pickToday(); }}>
                            Today
                        </div>

                        <div className={style.dateOption} onClick={() => { pickYesterday(); }}>
                            Yesterday
                        </div>

                        <div className={style.dateOption} onClick={() => { pickCustom(); }} style={{ marginBottom: 8 }}>
                            Choose custom date
                        </div>

                        {tempDateFilter.type === "custom" && (
                            <div style={{ marginTop: 8 }}>
                                <div style={{ display: "flex", gap: 8 }}>
                                    <input type="date" className={style.dateInput} value={tempDateFilter.from || ""} onChange={(e) => setTempFrom(e.target.value)} />
                                    <input type="date" className={style.dateInput} value={tempDateFilter.to || ""} onChange={(e) => setTempTo(e.target.value)} />
                                </div>

                                <div style={{ display: "flex", gap: 8, marginTop: 10, justifyContent: "flex-end" }}>
                                    <button className={style.btnCancel} onClick={cancelDateModal}>Cancel</button>
                                    <button className={style.btnApply} onClick={() => {
                                        if (!tempDateFilter.from || !tempDateFilter.to) {
                                            alert("Pick both From and To dates.");
                                            return;
                                        }
                                        if (tempDateFilter.from > tempDateFilter.to) {
                                            alert("From date cannot be after To date.");
                                            return;
                                        }
                                        applyDateModal();
                                    }}>Apply</button>
                                </div>
                            </div>
                        )}

                        {tempDateFilter.type === "today" && (
                            <div style={{ display: "flex", gap: 8, marginTop: 10, justifyContent: "flex-end" }}>
                                <button className={style.btnCancel} onClick={cancelDateModal}>Cancel</button>
                                <button className={style.btnApply} onClick={applyDateModal}>Apply</button>
                            </div>
                        )}
                        {tempDateFilter.type === "yesterday" && (
                            <div style={{ display: "flex", gap: 8, marginTop: 10, justifyContent: "flex-end" }}>
                                <button className={style.btnCancel} onClick={cancelDateModal}>Cancel</button>
                                <button className={style.btnApply} onClick={applyDateModal}>Apply</button>
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* DOWNLOAD MODAL */}
            {showDownloadModal && (
                <>
                    <div className={style.sectionOverlay} onClick={() => setShowDownloadModal(false)}></div>

                    <div className={style.downloadCenterModal}>
                        <button className={style.centerClose} onClick={() => setShowDownloadModal(false)}>✕</button>

                        <div className={style.centerItem} onClick={() => downloadData("pdf")}>PDF</div>
                        <div className={style.centerItem} onClick={() => downloadData("csv")}>CSV</div>
                        <div className={style.centerItem} onClick={() => downloadData("excel")}>Excel (.xlsx)</div>
                        <div className={style.centerItem} onClick={() => downloadData("txt")}>Text</div>
                    </div>
                </>
            )}
        </div>
    );
}
