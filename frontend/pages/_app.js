import { AuthProvider } from "../lib/auth";
import { ThemeProvider } from "../components/ThemeContext";
import { ToastProvider } from "../components/ToastContext";
import "../styles/globals.css";

export default function App({ Component, pageProps }) {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <Component {...pageProps} />
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}
