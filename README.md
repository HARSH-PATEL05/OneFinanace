
<div align="center">
    <h1>🚀 <b>OneFinance</b></h1>
    <h3><b>AI Powered Personal Finance + Stock Market Intelligence System</b></h3>
</div>

<br/>

---

# 🎯 <b>Project Overview</b>

<p>
<b>OneFinance</b> is a next–generation AI-driven financial ecosystem combining:
</p>

<ul>
  <li>🤖 <b>AI Stock Analysis (Sahayak)</b></li>
  <li>📊 <b>Portfolio & Mutual Fund Tracking</b></li>
  <li>🏦 <b>Bank Account Aggregation</b></li>
  <li>📱 <b>Android Auto-Sync Transaction Engine</b></li>
  <li>📈 <b>TradingView-style technical charting</b></li>
  <li>🧾 <b>Full Fundamental + Technical Research</b></li>
</ul>

⚡ No external user data is stored permanently — everything uses **runtime caching + live APIs**.

---

# 🧠 <b>Major Modules</b>

---

# 🟦 <h2>1️⃣ Sahayak – AI Stock Research Assistant</h2>

Your personal **AI market analyst**, performing both **fundamental** and **technical** deep research.

---

## 🔍 <b>Fundamental Research Engine</b>

Extracted using **NSE + YFinance**:

<ul>
  <li>🏢 Company Profile</li>
  <li>📊 Market Data</li>
  <li>📅 52-Week High/Low</li>
  <li>💰 PE / PB / Valuation Metrics</li>
  <li>📈 Profitability Ratios</li>
  <li>📉 Growth Metrics</li>
  <li>💵 Dividend Strength</li>
  <li>🧾 Financial Health (Debt/Cash)</li>
</ul>

---

## 📊 <b>AI Technical + Predictive Analysis</b>

The AI generates:

- 🔼 Movement Prediction (Up/Down/Sideways)  
- 📈 Confidence Score  
- 💹 Next-day price prediction  
- ⚙️ Technical Indicator Summary  
- 📊 Trend (Short/Medium/Long)  
- 🧭 Pivot Levels  
- 🟩 Support & Resistance  
- 🟦 Swing Levels  
- 🟥 Multi-Timeframe Levels  
- 🧠 AI-written Summary  

---

# 🟩 <h2>2️⃣ Portfolio Section (Stocks + Mutual Funds)</h2>

---

## 📌 <b>Stock Portfolio Features</b>

- Add/Edit/Delete Stocks  
- Auto-refreshing LTP  
- Avg Buy Price  
- Total Value  
- Absolute & % P/L  
- Portfolio Allocation Chart  
- Historical Trend Chart  
- Backend DB Sync  

---

## 📌 <b>Mutual Fund Portfolio (MF Support)</b>

Includes:

- Fund Name  
- NAV  
- Units  
- Category  
- Invested Amount  
- Current Value  
- Absolute P/L  
- MF API Auto Refresh  
- Pie Chart (MF+Stocks Combined)  
- XIRR (coming soon)  

This turns Portfolio into a **complete investment dashboard**.

---

# 🟥 <h2>3️⃣ Account Section – Fully Completed</h2>

Split into **3 robust modules**:

---

## 🟦 <b>1️⃣ Account Overview</b>

Shows all bank accounts as cards:

- Bank Name  
- Account Type  
- Masked Number  
- Balance  
- Last Updated  
- Sync Status  

Live updates from Android app.

---

## 🟧 <b>2️⃣ Transaction History</b>

A powerful banking timeline:

### 🔎 Filters:
- Bank  
- UPI / ATM / NEFT / Card  
- Date Range  
- Sorting  

### 📜 Details:
- Amount  
- Type (CR/DR)  
- Mode  
- UPI ID  
- Reference No.  
- Balance After Txn  
- Smart Categorization  

### ⚠️ Advanced Logic:
- Auto-detects missing transactions  
- Fixes incorrect balances  
- Reconstructs ledger when mismatch occurs  

---

## 🟩 <b>3️⃣Chart section- Analytics & Insights</b>

Includes:

- 📈 Monthly Spend Chart  
- 💵 Income vs Expense  
- 🥧 Category Pie Chart  
- 📊 Cashflow Over Time  
- 🏧 ATM Summary  
- 🧾 UPI App Breakdown  
- 🔔 High-value alerts (coming soon)  



---

# 📱 <h2>Android SMS Parser App</h2>

Your phone becomes a real-time **bank statement generator**.

✔ Reads SMS  
✔ Parses bank details  
✔ Finds UPI / ATM / NEFT / IMPS  
✔ Extracts account balance  
✔ Room DB Storage  
✔ Sync with backend every minute  
✔ Sends only unsynced data  
✔ Auto missing transaction detection  

This is the backbone of the **Account Section**.

---

# 🎨 <h2>Frontend Architecture (React + Vite)</h2>

Includes:

- Responsive 3-column grids  
- Fullscreen charts  
- Cached fundamentals  
- Cached AI analysis  
- Clean UI  

---

# 🧭 <h2>Roadmap</h2>

<table>
<tr><th>Feature</th><th>Status</th></tr>
<tr><td>Account System</td><td>✅ Completed</td></tr>
<tr><td>Portfolio System</td><td>✅ Completed</td></tr>
<tr><td>Mutual Fund Support</td><td>✅ Completed</td></tr>
<tr><td>AI Fundamental Analysis</td><td>✅ Completed</td></tr>
<tr><td>AI Technical Charts</td><td>✅ Completed</td></tr>
<tr><td>Android SMS App</td><td>✅ Completed</td></tr>
<tr><td>Multi-timeframe OHLC API</td><td>🔄 In Progress</td></tr>
<tr><td>Redis OHLC Cache</td><td>🔄 In Progress</td></tr>
<tr><td>TradingView-like Editor</td><td>🔜 Planned</td></tr>
<tr><td>Indicators Library</td><td>🔜 Planned</td></tr>
<tr><td>Drawing Tools</td><td>🔜 Planned</td></tr>
<tr><td>Alerts System</td><td>🔜 Planned</td></tr>
<tr><td>Full Trading Terminal</td><td>🤯 Future</td></tr>
</table>

---

# 🛠️ <h2>How to Run</h2>

## 🔧 Backend
cd Backend
pip install -r requirements.txt
uvicorn app.main:app --reload


## 💻 Frontend
cd Frontend
npm install
npm run dev

<br/>
❤️ <h2>Support & Contributions</h2>
If you like this project, please ⭐ star the repo.
Contributions, issues, and feature requests are welcome.
<br/>
📄 <h2>License</h2>
This project is for personal & educational use.
Commercial usage requires permission.

<br/> <div align="center"> <b>Made with ❤️ by Harsh Patel</b> </div> ```