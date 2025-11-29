import { Outlet, NavLink } from "react-router-dom";
import { useState } from "react";
import style from "./Style/Home.module.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import Bankaccount from "./accountsection/Bankaccount"; 
import Chart from "./accountsection/Chart"; 
import Transaction from "./accountsection/Transaction"; 
function Home() {
    return (
        <>
            <div className={style.main}>
                <div className={style.bankname}>
                    <Bankaccount />
                </div>
                <div className={style.chart}>
                    <Chart />
                </div>
                <div className={style.txn}>
                    <Transaction />
                </div>
            </div>
        </>
    )
}
export default Home