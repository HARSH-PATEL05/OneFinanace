import axios from "axios";

// Base API instance
const API = axios.create({
  baseURL: "http://localhost:8000",
});

/* ============================================================
   PORTFOLIO (unchanged)
=============================================================== */
export const fetchAllPortfolios = async () => {
  try {
    const res = await API.get("/brokers/portfolio");
    return res.data;
  } catch (err) {
    console.error("Error fetching portfolios:", err);
    return {};
  }
};

export const fetchLiveHoldingsLTP = async () => {
  try {
    const res = await API.get("/live/holdings-ltp");
    return res.data;
  } catch (err) {
    console.error("Error fetching live LTP:", err);
    return [];
  }
};

export const fetchDailyStockSnapshot = async () => {
  try {
    const res = await API.get("/live/holdings");
    return res.data;
  } catch (err) {
    console.error("Error fetching daily stock snapshot:", err);
    return [];
  }
};

export const fetchDailyMfSnapshot = async () => {
  try {
    const res = await API.get("/live/mfs");
    return res.data;
  } catch (err) {
    console.error("Error fetching daily MF snapshot:", err);
    return [];
  }
};

/* ============================================================
   MARKET STATUS API (for smart polling + schedule control)
=============================================================== */

export const fetchMarketStatus = async () => {
  try {
    const res = await API.get("/live/market-status");
    return res.data;  // { open, state, nextCheckSeconds }
  } catch (err) {
    console.error("Error fetching market status:", err);
    return {
      open: false,
      state: "Error",
      nextCheckSeconds: 300, // fallback 5 min
    };
  }
};


/* ============================================================
   ACCOUNT API (same as your previous but corrected)
=============================================================== */
export const listAccounts = async () => {
  try {
    const res = await API.get("/accounts");
    return res.data;
  } catch (err) {
    console.error("Error fetching accounts:", err);
    return null;
  }
};

export const createAccount = async (payload) => {
  try {
    const res = await API.post("/accounts", {
      bank_name: payload.bank,                 // backend expects bank_name here
      acronym: payload.acronym,
      account_number: payload.number,
      holder_name: payload.holder || "",
      current_balance: payload.balance === "" ? 0 : Number(payload.balance),
    });
    return res.data;
  } catch (err) {
    console.error("Error creating account:", err);
    return null;
  }
};

export const updateAccount = async (account_number, payload) => {
  try {
    const res = await API.put(`/accounts/${account_number}`, {
      bank_name: payload.bank,
      acronym: payload.acronym,
      holder_name: payload.holder,
      current_balance: payload.balance === "" ? 0 : Number(payload.balance),
    });
    return res.data;
  } catch (err) {
    console.error("Error updating account:", err);
    return null;
  }
};

export const deleteAccountApi = async (account_number) => {
  try {
    const res = await API.delete(`/accounts/${account_number}`);
    return res.data;
  } catch (err) {
    console.error("Error deleting account:", err);
    return null;
  }
};

/* ============================================================
   TRANSACTIONS API (NEW + matches your fixed backend)
=============================================================== */

/**
 * Fetch transactions.
 * If accountNumber === "ALL" → calls /transactions/all
 * Else → calls /transactions/{account_number}
 */
export const fetchTransactions = async (accountNumber = "ALL") => {
  try {
    if (!accountNumber || accountNumber === "ALL") {
      const res = await API.get("/transactions/all");
      return res.data || [];
    } else {
      const res = await API.get(
        `/transactions/${encodeURIComponent(accountNumber)}`
      );
      return res.data || [];
    }
  } catch (err) {
    console.error("Error fetching transactions:", err);
    return [];
  }
};

/**
 * Delete ALL transactions
 */
export const deleteAllTransactions = async () => {
  try {
    const res = await API.delete("/transactions");
    return res.data;
  } catch (err) {
    console.error("Error deleting all transactions:", err);
    throw err;
  }
};

/**
 * Delete transactions for one specific account_number
 */
export const deleteTransactionsForAccount = async (accountNumber) => {
  try {
    const res = await API.delete(
      `/transactions/${encodeURIComponent(accountNumber)}`
    );
    return res.data;
  } catch (err) {
    console.error("Error deleting transactions for account:", err);
    throw err;
  }
};

/**
 * Run AI Stock Analysis for a specific symbol
 */
export const analyzeStock = async (symbol) => {
  try {
    const res = await API.post(
      "/ai-analysis/analyze",
      { symbol: symbol }
    );
    return res.data; // return backend JSON
  } catch (err) {
    console.error("Error analyzing stock:", err);
    throw err;
  }
};
/**
 * Get fundamental data for a specific stock symbol
 */
export const getFundamentals = async (symbol) => {
  try {
    const res = await API.post(
      "/ai-analysis/fundamentals",
      { symbol: symbol }
    );
    return res.data; // return backend JSON
  } catch (err) {
    console.error("Error fetching fundamentals:", err);
    throw err;
  }
};
