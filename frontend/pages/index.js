import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    const token = sessionStorage.getItem("metroflow_token");
    window.location.href = token ? "/dashboard" : "/login";
  }, []);
  return null;
}
