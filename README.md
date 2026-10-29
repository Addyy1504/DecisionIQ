# DecisionIQ
### AI-Powered Analytics & Machine Learning Platform

DecisionIQ is an end-to-end business analytics and decision intelligence platform combining SQL, Artificial Intelligence, Machine Learning, and interactive dashboards to support data-driven business decisions.

The platform uses a synthetic e-commerce dataset to analyze business performance, segment customers, predict product return risks, and answer natural-language business questions.

---

## TECH STACK

**Languages:** Python, SQL, JavaScript

**Backend:** FastAPI, MySQL, Pandas, NumPy

**Machine Learning:** scikit-learn, K-Means, Logistic Regression, Random Forest

**AI:** OpenAI API, Natural Language-to-SQL

**Frontend:** React, Vite, Recharts

---

## DATASET OVERVIEW

DecisionIQ is built on a synthetic e-commerce dataset containing:

- 60,000 orders
- Approximately 180,000 order items
- 15,000 customers
- 200,000 website sessions
- 500 products
- Marketing campaigns, campaign performance, and returns data

The data is stored in MySQL and analyzed through reusable SQL views and Python-based analytical modules.

---

## KEY FEATURES

### 1. AI-Powered Business Analyst

An AI analyst that converts natural-language business questions into SQL queries and generates analytical insights.

- Natural-language-to-SQL generation
- SQL error detection and automatic repair
- Multi-intent analytical queries
- Business-oriented explanations
- Dynamic charts and visualizations

Example questions:
- Which category generates the most profit?
- Why is Fashion underperforming?
- How does mobile conversion compare to desktop?
- Which months show unusual revenue movements?

### 2. Business Analytics & Intelligence

Implemented analytical modules covering:

- Revenue, gross profit, profit margin, and AOV
- Product and category profitability
- Website conversion funnel analysis
- Return rates and refund analysis
- Marketing ROAS and CPA
- Discount what-if simulations
- Monthly anomaly analysis

### 3. Customer Segmentation — Machine Learning

Implemented RFM-based customer segmentation using K-Means clustering.

Process:
- Extracted Recency, Frequency, and Monetary features.
- Standardized features using StandardScaler.
- Evaluated cluster counts using Silhouette Score.
- Selected K = 3 and interpreted customer profiles.

Identified three customer segments:
- At Risk
- Regular Customers
- High-Value Loyal

The platform supports segment-level analysis, customer targeting, and CSV exports.

### 4. Return Risk Prediction — Machine Learning

Developed a supervised classification pipeline to predict the probability of order-item returns.

Models:
- Logistic Regression
- Random Forest

Methodology:
- Historical feature engineering
- Data preprocessing and encoding
- Temporal train/test splitting
- Data leakage prevention
- Model comparison and evaluation

Evaluation Metrics:
Accuracy, Precision, Recall, F1 Score, ROC-AUC

**Best Result:** Logistic Regression achieved approximately 0.60 ROC-AUC.

The model is experimental because the synthetic dataset contains limited predictive signals. It is not intended for production-grade automated decisions.

---

## APPLICATION ARCHITECTURE

React Frontend
       |
       v
FastAPI Backend
       |
       +-- AI Analyst (OpenAI API + SQL)
       |
       +-- Business Analytics (SQL + Pandas)
       |
       +-- Machine Learning (scikit-learn)
       |
       v
MySQL Database

The React application provides interactive dashboards for business analytics, customer segmentation, and return-risk predictions.

---

## PROJECT STRUCTURE

```text
DecisionIQ/
|-- backend/          Python, FastAPI, AI and ML modules
|-- frontend/         React application
|-- sql/              Database schema and analytical queries
|-- data/             Synthetic e-commerce datasets
|-- docs/             Project documentation
|-- assets/           Architecture and screenshots
|-- generate_data.py  Dataset generation
|-- requirements.txt  Python dependencies
|-- README.md         Project documentation
```

---

## PROJECT STATUS

**Active Development**

Current implementation includes:
- AI-powered SQL analytics
- Business KPI analysis and simulations
- RFM-based customer segmentation
- Return-risk classification models
- Interactive React dashboards
- FastAPI backend integration

Planned improvements:
- Further model experimentation and evaluation
- Improved frontend visualizations
- Automated testing and documentation
- Deployment and performance optimization

