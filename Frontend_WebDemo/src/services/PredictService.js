import axios from "axios";

const BASE_URL = "http://localhost:5000/api";

export const predictCSV = async (file, nDays) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("n_days", nDays);
  const res = await axios.post(`${BASE_URL}/predict/csv`, formData);
  return res.data;
};

export const predictManual = async (history, nDays) => {
  const res = await axios.post(`${BASE_URL}/predict/manual`, {
    history,
    n_days: nDays,
  });
  return res.data;
};
