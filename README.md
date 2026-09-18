## Contributing Guidelines (For Interns / Collaborators)

All interns added as collaborators to this repository must follow the branch workflow below. **Direct commits or pushes to the `main` branch are not allowed.**

> Note: `main` only contains the `LICENSE` and `README.md` — it is not used for active development. There is no need to pull the latest `main` into your branch at any point.

### 1. Branch Naming

- Every intern must create their own branch off `main`, named after themselves.
- Suggested naming convention: `firstname-lastname` (all lowercase, hyphen-separated).
  - Example: `john-doe`, `aisha-khan`

### 2. How to Create Your Branch

**Option A — Clone and push (recommended)**

```bash
# Clone the repository
git clone https://github.com/springboardmentor443m-coder/Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization.git

# Move into the project folder
cd Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization

# Create and switch to your own branch (off main)
git checkout -b your-name

# ... make your changes ...

# Stage, commit, and push your changes to YOUR branch only
git add .
git commit -m "Describe your change here"
git push origin your-name
```

**Option B — GitHub UI upload**

1. Go to the repository on GitHub.
2. Switch the branch dropdown from `main` to your own branch (create it first via **Branch: main → View all branches → New branch**, named after yourself).
3. Once on your branch, use **Add file → Upload files** to upload your code.
4. Commit directly to your branch (not `main`).

### 3. Rules

- ❌ Do **not** push or upload code directly to `main`.
- ❌ Do **not** push code to another intern's branch.
- ✅ Only push/upload code to the branch that carries your own name.
- Keep uploading/pushing your code to your branch regularly as you make progress. No pull requests are required — your branch itself is the deliverable.

### 4. Summary

| Action | Allowed? |
|---|---|
| Push to `main` directly | ❌ No |
| Create your own branch from `main` | ✅ Yes |
| Push/upload code to your own branch | ✅ Yes |
| Push/upload code to someone else's branch | ❌ No |
| Open a Pull Request | Not required |


## Vijaya Sree Progress Update

### Completed
- Dataset Selection (NYC Subway Traffic 2017–2021)
- Data Cleaning & Preprocessing
- Feature Engineering (Temporal & Spatial Variables)
- Exploratory Data Analysis (`01_EDA.ipynb`)
- **Target Leakage Investigation & Prevention Strategy**
- **Machine Learning Model Training & Benchmarking** (Decision Tree, Random Forest, XGBoost)
- **Automated Model Selection & Serialization** (`models/congestion_model.pkl`)
- **Real-Time Prediction & Recommendation Engine** (`src/prediction.py`)
- **Model Training Walkthrough Notebook** (`notebooks/02_Model_Training.ipynb`)
- **FastAPI Real-Time Prediction Backend** (`api/main.py`)

---

### Machine Learning Model Evaluation & Comparison

Models were trained and evaluated using stratified 80/20 train-test splits on clean, non-leaked features (150,000 balanced records):

| Model | Accuracy | F1 (Weighted) | Precision (Weighted) | Recall (Weighted) | Training Time |
|---|---|---|---|---|---|
| **Decision Tree (Baseline)** | 87.64% | 0.8760 | 0.8761 | 0.8764 | 0.88s |
| **Random Forest (Selected)** | **88.07%** | **0.8799** | **0.8801** | **0.8807** | 8.14s |
| **XGBoost Classifier** | 86.05% | 0.8594 | 0.8590 | 0.8605 | 6.83s |

**Automated Selection**: **Random Forest Classifier** achieved the highest weighted F1 Score (**0.8799**) and highest accuracy (**88.07%**), outperforming the baseline Decision Tree and XGBoost while demonstrating exceptional generalization across all 3 congestion tiers:
- **High Congestion**: Precision: 0.9072, Recall: 0.9496, F1: 0.9279
- **Low Congestion**: Precision: 0.8930, Recall: 0.8373, F1: 0.8643
- **Medium Congestion**: Precision: 0.8324, Recall: 0.8174, F1: 0.8248

---

### Target Leakage Prevention Strategy

- **Observation**: `Total_Traffic` is mathematically defined as `Entries + Exits`, and `Congestion_Level` was defined directly from the 33rd and 66th quantiles of `Total_Traffic`.
- **Leakage Experiment**:
  - Model A (Clean: Temporal + Station Features): **87.08%** Accuracy.
  - Model B (Leaked: Temporal + Station + Entries + Exits): **99.15%** Accuracy.
- **Decision**: In real-world transit operations, future passenger entry/exit numbers are unavailable in advance. Feeding `Total_Traffic`, `Entries`, or `Exits` into the model causes target leakage. Therefore, the production model strictly relies on scheduled temporal and station coordinates (`hour`, `day_of_week`, `is_peak_hour`, `Latitude`, `Longitude`, `Borough`, `Structure`, `Stop Name`).

---

### Top Feature Importances (Random Forest)

1. **`hour` (27.99%)**: Captures major peak commuting windows (morning rush 8–9 AM, evening rush 5–7 PM) vs. overnight minimums.
2. **`Latitude` (18.52%) & `Longitude` (17.04%)**: Spatial positioning distinguishes high-density Manhattan commercial corridors from outer residential terminals.
3. **`Stop Name` (13.17%)**: Station-specific passenger capacity and major transfer hubs (e.g., Grand Central, Times Square).
4. **`Structure` (5.24%) & `day_of_week` (4.35%)**: Underground subway hubs vs elevated stations, and weekday vs weekend commuting dynamics.

---

### Files Added & Updated

```text
api/
└── main.py                   # FastAPI application with /predict, /health, Swagger docs

dashboard/
└── app.py                    # Multi-page interactive Streamlit transit intelligence dashboard

src/
├── data_cleaning.py          # Data ingestion and deduplication
├── feature_engineering.py    # Temporal and congestion feature extraction
├── utils.py                  # Data loading, validation, encoding, metrics, plots, persistence
├── train_model.py            # Training pipeline, leakage experiment, model comparison & export
└── prediction.py             # Inference engine (single, batch, confidence, recommendations)

models/
├── congestion_model.pkl      # Production model bundle (model, encoders, metadata)
└── model.pkl                 # Compatibility alias

reports/figures/
├── confusion_matrix.png      # Confusion matrix heatmap for the selected model
└── feature_importance.png    # Feature importance horizontal bar chart

notebooks/
├── 01_EDA.ipynb              # Exploratory data analysis
└── 02_Model_Training.ipynb   # Model training, comparison, leakage analysis, and evaluation
```

---

### How to Run

1. **Train and compare models**:
   ```bash
   python src/train_model.py
   ```

2. **Run real-time prediction CLI**:
   ```bash
   python src/prediction.py
   ```

3. **Launch FastAPI Backend Server**:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```
   - Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
   - ReDoc Documentation: `http://127.0.0.1:8000/redoc`
   - Health Check: `http://127.0.0.1:8000/health`

4. **Launch Interactive Streamlit Dashboard**:
   ```bash
   streamlit run dashboard/app.py
   ```
   - Dashboard UI: `http://localhost:8501`

---

### Upcoming
- Traffic Forecasting (Time-Series / Demand Estimation)