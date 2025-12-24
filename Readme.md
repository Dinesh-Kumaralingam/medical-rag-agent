Pathfinder Health Agent 🏥

An AI-powered medical triage assistant built with **Python**, **Streamlit**, and **Google Gemini Pro**.

## 🚀 Overview
Pathfinder is a RAG-based (Retrieval-Augmented Generation) agent designed to bridge the gap between symptom analysis and healthcare logistics. It interprets natural language symptoms, estimates severity, and routes patients to optimal care facilities based on geospatial data.

## 🛠️ Tech Stack
* **LLM Engine:** Google Gemini Pro via API
* **Framework:** Streamlit (Python)
* **Geospatial:** Folium (Map Integration)
* **Data Processing:** Pandas, FuzzyWuzzy (String Matching)

## ⚡ Key Features
* **Symptom Triage:** Uses Chain-of-Thought prompting to assess emergency severity (Low/Medium/High).
* **Location Routing:** Calculates distance to nearest hospitals using latitude/longitude data.
* **Cost Estimation:** Provides insurance-adjusted cost estimates for urgent care vs. ER visits.

## 📦 How to Run
1. Clone the repo:
   ```bash
   git clone [https://github.com/Dinesh-Kumaralingam/pathfinder-health-agent.git](https://github.com/Dinesh-Kumaralingam/pathfinder-health-agent.git)
Install dependencies:

Bash

pip install -r requirements.txt
Run the app:

Bash

streamlit run app.py

3.  Save it.
4.  Run these commands again to update GitHub:
    ```powershell
    git add README.md
    git commit -m "Add documentation"
    git push
    ```

**Now, go to your Portfolio website code and update the "Pathfinder" card link to point to this GitHub repository.**