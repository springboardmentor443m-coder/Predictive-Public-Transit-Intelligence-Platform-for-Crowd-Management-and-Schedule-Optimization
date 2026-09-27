import { Html, Head, Main, NextScript } from "next/document";

const THEME_BOOTSTRAP = `(function(){try{var t=localStorage.getItem("metroflow_theme"),d=document.documentElement;if(t==="light"){d.classList.add("light");d.classList.remove("dark")}else{d.classList.add("dark");d.classList.remove("light")}}catch(e){}})();`;

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </Head>
      <body>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
