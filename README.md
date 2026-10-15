AI MetroFlow
Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization
AI MetroFlow is a prototype that combines machine learning, historical passenger-traffic analytics, demand forecasting, and a transit-operations dashboard. It demonstrates how historical subway traffic patterns can support congestion assessment and planning recommendations.
Important scope note: The current prototype uses historical NYC subway turnstile data and simulated train information. It is not connected to a verified live MTA feed, live passenger-counting sensors, or real train-dispatch systems. Predictions are generated from submitted inputs; train positions and scheduling recommendations are demonstrations, not operational commands.

Table of Contents
- Problem Statement
- Objectives
- Features
- Technology Stack
- Architecture
- Machine Learning
- Dataset
- Project Structure
- Installation
- Run the Application
- API
- Screenshots
- Limitations
- Future Work
- Push to GitHub
Problem Statement
Transit operators need to understand passenger-flow patterns, identify potential congestion, and plan service levels. Historical turnstile records reveal traffic patterns by station and time, but they do not directly measure how many people are physically inside a station at a given moment.
AI MetroFlow demonstrates a workflow that analyzes historical entry/exit events, predicts a congestion category for supplied station/time features, estimates numerical traffic demand, and presents planning suggestions in a dashboard.
Objectives
- Analyze historical passenger traffic across stations and time periods.
- Classify supplied observations as Low, Medium, or High congestion.
- Estimate numerical passenger traffic for supported forecast horizons.
- Present analytics, predictions, alerts, and scheduling suggestions in one interface.
- Demonstrate data-driven planning while keeping suggestions separate from real-world train control.
Features
The current dashboard has been reported to include:
1. Overview & Console — project and system summary.
2. Crowd Monitoring — station-level traffic and congestion views.
3. Live Train Tracking — simulated train positions and statuses.
4. Schedule Management — frequency/headway suggestions using configurable prototype rules.
5. Alerts & Incident Center — alert display and handling workflow.
6. Real-Time Prediction — on-demand model inference from submitted inputs. “Real-time” means a prediction is generated when requested, not that live sensor data is streamed.
7. Demand Forecasting — numerical traffic estimates for horizons such as 1 hour, 3 hours, and 24 hours.
8. Dataset Analytics & EDA — summaries and traffic-pattern analysis.
Confirm each feature in the current running version before describing it as production-ready.
Technology Stack
- Language / ML: Python, pandas, NumPy, scikit-learn; XGBoost was included in model comparisons.
- Backend: FastAPI and Uvicorn.
- Frontend: React and Vite.
- Model artifacts: serialized .pkl files.
- Version control: Git and GitHub.
Architecture
Historical NYC subway turnstile records
                 |
                 v
      Data cleaning and validation
                 |
                 v
       Feature engineering and EDA
                 |
          +------+------+
          |             |
          v             v
 Congestion classifier  Demand regressor
          |             |
          +------+------+
                 |
                 v
           FastAPI backend
                 |
                 v
        React + Vite dashboard
                 |
                 v
 Predictions, analytics, alerts, and
 illustrative schedule recommendations
This is a high-level architecture. Check the current source code for the exact feature pipeline and connections between modules.
Machine Learning
Congestion classification
The classifier predicts one of three categories: Low, Medium, or High. The dashboard may show the predicted category, class probabilities/confidence where available, and a recommendation. The model predicts from supplied features; it does not directly count people in a station.
Candidate classifiers evaluated reportedly included Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, AdaBoost, and XGBoost. The reported selected model is a Random Forest Classifier. A previous evaluation reported approximately 87% accuracy. Replace this with the final reproducible evaluation result before publishing a formal metric.
Passenger-demand forecasting
The forecasting model produces a numerical traffic estimate, not a Low/Medium/High category. Supported dashboard horizons have been reported as:
- 1 hour
- 3 hours
- 24 hours
Random Forest Regressor and XGBoost Regressor were compared; the reported selected model is a Random Forest Regressor. Its target is based on historical traffic counts (entry/exit events), not a guaranteed count of future unique passengers.
Previously reported Random Forest regression metrics were R² = 0.8537, RMSE = 1430.38, and MAE = 568.67. Verify these against the final evaluation artifacts and validation methodology before publishing them.
Scheduling recommendations
The prototype maps congestion categories to suggested service intervals/headways. These are configurable demonstration rules, not official MTA schedules and not automatic dispatch instructions. Any capacity or throughput estimate depends on assumptions configured in the application.
Dataset
The project has used historical NYC subway turnstile records, reported as approximately 4.59 million records from the 2017–2021 period. The data includes passenger entry/exit counts and station/time-related information.
Preprocessing may include data cleaning, validation, creation of time-related features, calculation of traffic from entries and exits, and preparation of labels/features. Consult the current preprocessing scripts for the exact operations and feature list.
Interpretation caveats
- Entry/exit events are not the same as the number of people currently inside a station.
- Historical turnstile counts are not live occupancy measurements.
- Congestion labels depend on the project's labeling method and thresholds.
- Do not describe this as a live MTA integration unless one has been implemented and verified.
Project Structure
This is a guide to the main files previously reported; adjust it to match your actual repository tree.
Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization/
├── api/
│   └── main.py                 # FastAPI application
├── frontend/                   # React + Vite dashboard
├── src/
│   └── demand_forecasting.py   # Demand-forecasting workflow
├── models/
│   ├── congestion_model.pkl    # If included
│   └── demand_model.pkl        # If included
├── reports/
│   ├── forecast_results.csv    # If generated
│   └── figures/                # Generated figures, if present
├── notebooks/                  # If present
├── requirements.txt
├── .gitignore
└── README.md
Installation
Prerequisites
- Git
- Python 3.10+ (developed with Python 3.11)
- Node.js and npm
- Required model artifacts, unless regenerated by the training pipeline
1. Clone the repository
Replace <your-github-username> with the owner of the repository.
git clone https://github.com/<your-github-username>/Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization.git
cd Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization
2. Set up Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
3. Install frontend packages
cd frontend
npm install
cd ..
Run the Application
Open two PowerShell terminals from the project root.
Terminal 1 — Backend
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
- API base URL: http://127.0.0.1:8001
- Swagger UI: http://127.0.0.1:8001/docs
- Health endpoint: http://127.0.0.1:8001/health
The API needs its dependencies and required model artifacts. If it fails, inspect terminal errors and verify model paths and required input fields.
Terminal 2 — Frontend
cd frontend
npm run dev
Open the local URL printed by Vite, commonly http://localhost:5173/. Keep both terminals open.
API
The project has been reported to expose these endpoints. Confirm their current request/response schemas in api/main.py or Swagger UI.
Endpoint	Purpose
GET /health	Checks service status.
POST /predict	Accepts station/time-related inputs and returns a congestion prediction.


Illustrative request
An earlier API version used a request shaped like this. Check /docs before using it, because the current schema may differ.
{
  "hour": 8,
  "day": 15,
  "month": 9,
  "year": 2021,
  "day_of_week": 2,
  "Latitude": 40.7527,
  "Longitude": -73.9772,
  "Borough": "Manhattan",
  "Structure": "Subway",
  "Stop Name": "Grand Central - 42 St"
}
Response fields may include a congestion label, probabilities/confidence, and a recommendation. Verify exact response keys and values in the current endpoint implementation.
Screenshots
Put screenshots of the actual current application in docs/images/, then uncomment/update paths below.
Suggested images:
- docs/images/dashboard-overview.png
- docs/images/crowd-monitoring.png
- docs/images/congestion-model-evaluation.png
- docs/images/demand-forecasting.png
- docs/images/schedule-management.png
- docs/images/api-swagger.png
Example:
![Dashboard overview](docs/images/dashboard-overview.png)
![Congestion model evaluation](docs/images/congestion-model-evaluation.png)
![Demand forecasting](docs/images/demand-forecasting.png)
Use real screenshots, not mockups represented as live results. Remove personal information, credentials, tokens, and sensitive local paths before committing.
Limitations
- No verified live MTA API or passenger-sensor integration is currently confirmed.
- Train positions and statuses in the tracking view are simulated.
- On-demand prediction is not continuous live monitoring.
- Turnstile counts do not directly measure current station occupancy.
- Scheduling outputs are prototype suggestions; the application does not control actual trains.
- Metrics should be backed by reproducible evaluation and a clearly documented train/test or time-based split.
- If model files are too large or excluded from Git, document how to obtain or regenerate them.
Future Work
- Integrate an approved live transit feed and passenger-count data where available.
- Validate forecasts using time-ordered holdout data and compare with simple baselines.
- Add model monitoring, drift checks, and uncertainty reporting.
- Document alert creation and ID-generation logic.
- Evaluate scheduling suggestions against verified operating constraints.
- Add automated tests, continuous integration, and reproducible model training.
- Deploy only after security, reliability, and operational testing.
Push to GitHub
The internship workflow previously used the branch vijaya-sree-nethagani. Check your current repository state and remote before pushing. Do not push directly to main if your team requires the internship branch.
git status
git branch
git remote -v
After confirming the branch and remote:
git switch vijaya-sree-nethagani
git status
git add README.md
git add api frontend src reports requirements.txt .gitignore
git status
git diff --cached
git commit -m "Update AI MetroFlow project and documentation"
git push -u origin vijaya-sree-nethagani
Only stage paths that actually exist. If Git reports that a path does not exist, remove it from the command and stage the real folders/files. If the branch is not available locally, inspect git branch -a and coordinate with the repository owner before creating or switching branches. If origin is missing, add the correct repository URL with git remote add origin <repository-url>; do not add it again if it already exists.
Checklist before pushing
- Exclude .venv/, venv/, node_modules/, caches, .env files, credentials, and private data in .gitignore.
- Never commit API keys, passwords, or access tokens.
- Check .pkl models and generated datasets for size. GitHub blocks individual files larger than 100 MB; consider Git LFS or documented model regeneration/download steps for large artifacts.
- Review git status and git diff --cached before committing.
- Do not delete shared branches or force-push without permission.
Acknowledgement
AI MetroFlow is an AI-powered public-transit analytics prototype developed for learning and demonstration. Keep this README synchronized with the actual code, model metrics, API schema, and implemented capabilities.