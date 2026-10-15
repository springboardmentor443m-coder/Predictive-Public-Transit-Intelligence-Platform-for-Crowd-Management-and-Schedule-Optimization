# 🚇 MetroFlow –  AI Platform for Metro Crowd Management and Scheduling

MetroFlow is an enterprise-grade applied ML transit management platform engineered for high-density metro operations. Built on a **Zero-CCTV, Privacy-First Architecture**, MetroFlow processes live turnstile sensor telemetry to eliminate bottlenecks via automated headway optimization and predictive fleet dispatch.

---

##🏛️ System Architecture Flow
```text
[192 IoT Turnstiles] 
         │ (Live Taps Stream)
         ▼
[FastAPI Ingestion Engine] ──► [MongoDB Telemetry Store]
         │
         ▼
[Random Forest Regressor (Scikit-Learn)]
   ├── Peak Density Forecast (96.2% Conf)
   └── Automated Headway Decision Engine (e.g. 5.0m -> 2.8m)
         │
         ├───────────────────────────────┐
         ▼                               ▼
[React OCC Command Center]    [Multi-Channel Alert Broker]
   ├── SVG Topology Visualizer   ├── SendGrid Email
   ├── GPS Train Telemetry       ├── Twilio SMS & Voice
   └── Stream Settings Sliders   ├── FCM Push Notifications
                                 └── Platform PA Audio Synthesis
