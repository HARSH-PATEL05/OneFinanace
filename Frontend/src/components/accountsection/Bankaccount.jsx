import { useState, useEffect } from "react";
import style from "./Style/Bankaccount.module.css";
import "@fortawesome/fontawesome-free/css/all.min.css";

import {
  listAccounts,
  createAccount,
  updateAccount as updateAccountApi,
  deleteAccountApi
} from "@/Api";

/* ------------------------ Reusable Modal ------------------------ */
function Modal({ title, visible, onClose, children, footer }) {
  if (!visible) return null;
  return (
    <div className={style.overlay} onClick={onClose}>
      <div className={style.modal} onClick={(e) => e.stopPropagation()}>
        <h3 className={style.modalTitle}>{title}</h3>
        <div className={style.modalBody}>{children}</div>
        {footer && <div className={style.modalFooter}>{footer}</div>}
      </div>
    </div>
  );
}

export default function Bankaccount() {
  const [accounts, setAccounts] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [expanded, setExpanded] = useState(null);

  /** Account filter uses ACCOUNT_NUMBER (not id) */
  const [selectedFilter, setSelectedFilter] = useState("ALL");

  const initialForm = {
    bank: "",
    acronym: "",
    number: "",
    balance: "",
    holder: "",
  };

  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  // INSTANT LOAD FROM LOCAL STORAGE
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("accounts"));
      if (Array.isArray(saved)) {
        setAccounts(saved);   // show instantly
      }
    } catch (_) { }
  }, []);

  /* ---------------------------------------------------------
     LOAD ACCOUNTS FROM BACKEND
  ---------------------------------------------------------- */
  // BACKEND LOAD (REFRESH)
  useEffect(() => {
    (async () => {
      const backend = await listAccounts();

      if (backend) {
        const converted = backend.map((a) => ({
          id: a.id,
          number: String(a.account_number),
          bank: a.bank_name,
          acronym: a.acronym,
          balance: a.current_balance,
          holder: a.holder_name,
        }));

        setAccounts(converted);

        // IMPORTANT: update localStorage so next load is instant
        localStorage.setItem("accounts", JSON.stringify(converted));

        window.dispatchEvent(new Event("accountsUpdated"));
      }
    })();
  }, []);


  /* LOCAL BACKUP (optional failsafe) */
  useEffect(() => {
    localStorage.setItem("accounts", JSON.stringify(accounts));
  }, [accounts]);

  /* Restore previous selected filter */
  useEffect(() => {
    const saved = localStorage.getItem("selectedAccountFilter");
    if (saved) setSelectedFilter(String(saved));
  }, []);

  /* Update account filter + notify transaction page */
  const updateFilter = (value) => {
    const v = String(value);
    setSelectedFilter(v);
    localStorage.setItem("selectedAccountFilter", v);

    // tell Transaction.jsx to reload
    window.dispatchEvent(
      new CustomEvent("accountFilterChanged", { detail: v })
    );
  };

  /* ------------------ VALIDATION ------------------ */
  const validate = (data) => {
    const err = {};
    if (!data.bank.trim()) err.bank = "Enter bank name";
    if (!data.acronym.trim()) err.acronym = "Enter acronym";
    if (data.acronym.length < 2) err.acronym = "Min 2 chars";
    if (!data.number.trim()) err.number = "Enter account number";
    if (data.balance !== "" && isNaN(Number(data.balance)))
      err.balance = "Balance must be number";
    return err;
  };

  /* ------------------ OPEN MODALS ------------------ */
  const openAddModal = () => {
    setEditingId(null);
    setForm(initialForm);
    setErrors({});
    setShowAdd(true);
  };

  const openEditModal = (acc) => {
    setEditingId(acc.id); // SERIAL ID — used for updating
    setForm({
      bank: acc.bank,
      acronym: acc.acronym,
      number: acc.number, // account_number
      balance: acc.balance,
      holder: acc.holder,
    });
    setShowAdd(true);
  };

  /* ------------------ CONFIRM SAVE ------------------ */
  const handleConfirm = async () => {
    const data = {
      bank: form.bank.trim(),
      acronym: form.acronym.trim().toUpperCase(),
      number: form.number.trim(),
      balance: form.balance === "" ? "" : String(Number(form.balance)),
      holder: form.holder.trim(),
    };

    const err = validate(data);
    if (Object.keys(err).length) {
      setErrors(err);
      return;
    }

    /** UPDATE (uses account_number as path param) */
    if (editingId) {
      const accToEdit = accounts.find((a) => a.id === editingId);
      const res = await updateAccountApi(accToEdit.number, data);



      if (res) {
        setAccounts((prev) =>
          prev.map((a) =>
            a.id === editingId
              ? {
                ...a,
                bank: data.bank,
                acronym: data.acronym,
                number: data.number,
                balance: Number(data.balance),
                holder: data.holder,
              }
              : a
          )
        );
        window.dispatchEvent(new Event("accountsUpdated"));
      }
    }

    /** CREATE */
    else {
      const res = await createAccount(data);

      if (res) {
        const newAcc = {
          id: res.id,                                  // SERIAL ID
          number: String(res.account_number),          // Actual account number
          bank: res.bank_name,
          acronym: res.acronym,
          balance: res.current_balance,
          holder: res.holder_name,
        };
        setAccounts((prev) => [...prev, newAcc]);
        window.dispatchEvent(new Event("accountsUpdated"));

      }
    }

    setShowAdd(false);
    setEditingId(null);
    setForm(initialForm);
  };

  /* ------------------ DELETE ACCOUNT ------------------ */
  const handleDelete = async (id) => {
    if (!window.confirm("Delete this account?")) return;

    const acc = accounts.find((a) => a.id === id);

    const res = await deleteAccountApi(acc.number); // delete by account_number
    if (res) {
      setAccounts((prev) => prev.filter((a) => a.id !== id));
      window.dispatchEvent(new Event("accountsUpdated"));
      if (expanded === id) setExpanded(null);
      if (selectedFilter === acc.number) updateFilter("ALL");
    }
  };

  const toggleExpand = (id) => {
    setExpanded((cur) => (cur === id ? null : id));

  };

  /* ------------------- UI ------------------- */

  return (
    <>
      <div className={style.main}>
        <h2>Accounts</h2>

        {/* Filter */}
        <div className={style.filterContainer}>
          <select
            className={style.filterSelect}
            value={selectedFilter}
            onChange={(e) => updateFilter(String(e.target.value))}
          >
            <option value="ALL">All Accounts</option>

            {accounts.map((acc) => (
              <option key={acc.id} value={acc.number}>
                {acc.acronym} — {acc.bank}
              </option>
            ))}
          </select>
        </div>

        {/* ADD */}
        <div className={style.add}>
          <button onClick={openAddModal}>
            <i className="fa-solid fa-plus"></i> Add Account
          </button>
        </div>

        {/* LIST */}
        {accounts.length === 0 ? (
          <p className={style.noAcc}>No accounts yet</p>
        ) : (
          <div className={style.list}>
            {accounts.map((acc) => {
              const isOpen = expanded === acc.id;

              return (
                <div
                  key={acc.id}
                  className={`${style.accCard} ${isOpen ? style.open : ""}`}
                  onClick={() => toggleExpand(acc.id)}
                >
                  <div className={style.row}>
                    {/* Left side */}
                    <div className={style.left}>
                      <div className={style.acronym}>{acc.acronym}</div>
                      <div className={style.basicInfo}>
                        <div className={style.bankName}>{acc.bank}</div>
                        <div className={style.accNumber}>{acc.number}</div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div
                      className={style.actions}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        className={style.iconBtn}
                        onClick={() => openEditModal(acc)}
                        title="Edit"
                      >
                        <i className="fa-solid fa-pen-to-square"></i>
                      </button>

                      <button
                        className={style.iconBtn}
                        onClick={() => handleDelete(acc.id)}
                        title="Delete"
                      >
                        <i className="fa-solid fa-trash"></i>
                      </button>
                    </div>
                  </div>

                  {/* Expanded extra info */}
                  <div className={style.expanded}>
                    <div><strong>Holder:</strong> {acc.holder || "-"}</div>
                    <div><strong>Balance:</strong> {acc.balance}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ADD / EDIT Modal */}
      <Modal
        title={editingId ? "Edit Account" : "Add New Account"}
        visible={showAdd}
        onClose={() => setShowAdd(false)}
        footer={
          <>
            <button
              className={style.cancelBtn}
              onClick={() => {
                setShowAdd(false);
                setEditingId(null);
              }}
            >
              Cancel
            </button>

            <button className={style.confirmBtn} onClick={handleConfirm}>
              {editingId ? "Update" : "Confirm"}
            </button>
          </>
        }
      >
        {/* FORM INPUTS */}
        <label className={style.label}>Bank Name *</label>
        <input
          className={style.input}
          value={form.bank}
          onChange={(e) => setForm({ ...form, bank: e.target.value })}
        />
        {errors.bank && <div className={style.err}>{errors.bank}</div>}

        <label className={style.label}>Acronym *</label>
        <input
          className={style.input}
          value={form.acronym}
          onChange={(e) =>
            setForm({ ...form, acronym: e.target.value.toUpperCase() })
          }
        />
        {errors.acronym && <div className={style.err}>{errors.acronym}</div>}

        <label className={style.label}>Account Number *</label>
        <input
          className={style.input}
          value={form.number}
          onChange={(e) => setForm({ ...form, number: e.target.value })}
        />
        {errors.number && <div className={style.err}>{errors.number}</div>}

        <label className={style.label}>Available Balance</label>
        <input
          className={style.input}
          value={form.balance}
          onChange={(e) => setForm({ ...form, balance: e.target.value })}
        />
        {errors.balance && <div className={style.err}>{errors.balance}</div>}

        <label className={style.label}>Holder Name (optional)</label>
        <input
          className={style.input}
          value={form.holder}
          onChange={(e) => setForm({ ...form, holder: e.target.value })}
        />
      </Modal>
    </>
  );
}
