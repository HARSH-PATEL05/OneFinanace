import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

export const fetchAllPortfolios = async () => {
  const res = await API.get("/brokers/portfolio");
  console.log("Fetched MF data:", res);
  return res.data; // returns object: { zerodha: {holdings, mfs}, angelone: {...} }
};
