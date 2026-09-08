# 🚇 Predictive Crowd Monitoring & Train Scheduling

Welcome to the data processing and visualization pipeline for predictive crowd monitoring and train scheduling! 

> **🔗 Dataset Link:** [Download the Dataset (Excel Format)](https://docs.google.com/spreadsheets/d/1msXUYKOQ5EbkESvQkFJLWeE7W8WjB6KU/export?format=xlsx)

---

## 📥 Import the Dataset
The first step in our pipeline is loading the dataset directly from our Google Sheets export link for seamless analysis.

---

## 🧹 Data Inspection & Cleaning
Before diving into deep analysis, the data must be rigorously inspected and cleaned to ensure absolute accuracy. Our key areas of focus include:

*   **Missing Values:** We scan for any columns with `NaN` or `0` counts. If found, these are meticulously handled through imputation or dropping.
*   **Datetime Conversion:** Time columns are transformed from standard strings (objects) into robust `datetime` formats. Without this crucial step, the machine learning model cannot calculate critical metrics like delays or headways.
*   **Summary Statistics:** We review the minimum and maximum values for metrics like `Train_Occupancy_Count` and `Historical Delay (min)` to ensure there are no extreme outliers (e.g., negative passenger counts or a 5000-minute delay).

---

## ⚙️ Feature Engineering
Feature engineering is the art of translating raw data into a mathematical language that machine learning algorithms can actually understand. While a human instantly recognizes "2023-04-13 18:50:00" as the evening rush hour, an algorithm just sees a meaningless string of text. We break that raw data down into explicit, numerical signals.

### ⏰ Temporal Extraction
Machine learning models need time broken into distinct categories. We extract the exact hour and day of the week, and create binary flags (`1` or `0`) for business logic. For example, we flag two peak windows: 
*   **Morning Peak:** 8:00 AM – 11:59 AM
*   **Evening Peak:** 5:00 PM – 8:59 PM

### 🔄 Cyclical Encoding
Algorithms do not inherently know that Hour 23 (11 PM) and Hour 0 (Midnight) are right next to each other. If you just feed them numbers from 0 to 23, they assume midnight and 11 PM are as far apart as possible. To fix this, we apply **Sine and Cosine transformations** to the hour, teaching the model the continuous, circular loop of a 24-hour clock.

### 📏 Domain Metric Calculation
We combine existing columns to engineer the actual targets our model needs to predict. 
*   **Computed Delay:** Subtracting the `Scheduled_Departure_Time` from the `Actual_Departure_Time` gives us the exact delay in minutes. 
*   **Dwell Time:** Transit logic is applied to calculate exactly how long the train sits at the station (platform dwell time).

### 🔠 Label Encoding
Computers only look at math; they cannot read words like "Small" or "Large," nor can they multiply or split text like "Yellow Line" or "Rajiv Chowk." 
*   Label Encoding converts text into numbers so a computer can understand it, giving each unique category its own numerical ID (e.g., keeping order perfectly so `0 < 1 < 2`). 
*   Right before model training, string features are converted into binary arrays (One-Hot Encoding) or numerical IDs (Label Encoding).

---

## 📊 Data Visualisation
Visualisations are our lens to uncover hidden patterns, spot bottlenecks, and handle missing values within the dataset.

*   📈 **Train Occupancy Spikes (Boxplot):** Displays the distribution of train occupancy (passenger count) across the 24-hour format to easily identify hourly spikes in ridership.
*   🚨 **Platform Crowd Density Bottlenecks (Bar Plot):** Shows the average platform crowd density (passengers waiting) by hour of the day. This visualisation includes a visual reference line for a **"Critical Overcrowding Threshold"** set at 800 passengers to highlight rush hour bottlenecks and critical danger zones.

---

### Why Predict Train Occupancy?

While **Platform Density** alerts us to a *current* problem, **Train Occupancy** tells the system how to *solve* it. Forecasting occupancy allows the platform to:

*   **Prevent Platform Bottlenecks:** Anticipate when arriving trains are too full to clear waiting passengers, preventing dangerous exponential crowd buildup.
*   **Forecast Destination Outflow:** Proactively alert upcoming stations about massive incoming passenger volumes, enabling early exit gate and security management.
*   **Automate Schedule Optimization:** Differentiate between localized station flow issues and actual fleet capacity limits, dynamically decreasing headway intervals (e.g., from 6 to 3 minutes) only when demand requires it.

*   Platform Density tells you there is a problem right now.
*   Train Occupancy tells you how to fix the schedule to make that problem go away.

*   EXAMPLE SCENARIO FROM MY DATASET :

*   Imagine , the monitoring system detects 1,000 people on the platform at Rajiv Chowk. If the next train arrives but is already at 95% occupancy from previous stops, nobody on the crowded platform will be able to board. The platform crowd will continue to grow exponentially, creating a dangerous bottleneck. By predicting train occupancy, my system anticipates this failure before it happens.

