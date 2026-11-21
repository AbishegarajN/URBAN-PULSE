# URBAN PULSE – NYC 311 Service Requests Analytics Dashboard

## 1. Project Overview

URBAN PULSE is a data analytics project that explores New York City 311 Service Requests. It analyzes public service complaints to understand complaint patterns, agency workload, geographical distribution, and resolution performance.

The project uses Python, SQL, PostgreSQL, and Streamlit to transform raw service request data into meaningful insights through an interactive dashboard.

## 2. Project Objectives

- Analyze NYC 311 service request patterns.
- Identify the most common complaint categories.
- Understand service request distribution across boroughs.
- Examine agency workload and performance.
- Analyze complaint resolution times.
- Identify unusual resolution-time values using statistical methods.
- Present findings through an interactive dashboard.

## 3. Dataset

**Dataset:** NYC 311 Service Requests (2020 to Present)

**Source:** NYC Open Data

**Website:** https://opendata.cityofnewyork.us/

The project uses a dataset containing 100,000 records and 18 columns.

## 4. Technology Stack

- Python
- Pandas
- NumPy
- PostgreSQL
- SQL
- SQLAlchemy
- Streamlit
- Plotly
- Jupyter Notebook

## 5. Data Processing

The project includes:

- Data inspection and validation
- Missing-value analysis
- Duplicate-record checking
- Date and time conversion
- Feature engineering
- Resolution-time calculation
- IQR-based outlier detection
- PostgreSQL database integration

## 6. Dashboard Features

The interactive dashboard explores:

- Top complaint categories
- Agency workload distribution
- Borough-wise service request distribution
- Complaint status distribution
- Complaint resolution times
- Median resolution time by complaint category
- Median resolution time by agency
- Resolution-time outlier analysis
- Complaint closure-rate comparisons
- High-volume categories with long resolution times

## 7. Project Structure

The project includes the Streamlit application, data processing notebook, supporting datasets, visualizations, reports, and documentation.

## 8. How to Run the Project

1. Clone or download this repository.
2. Install the required Python packages.
3. Configure your PostgreSQL database connection.
4. Ensure the required dataset and database table are available.
5. Run the application:

```bash
streamlit run app.py
```

## 9. Expected Outcome

URBAN PULSE provides an interactive way to explore NYC 311 service requests and understand public complaint trends, geographical patterns, agency workload, and service resolution performance.

## 10. Author

**Project:** URBAN PULSE  
**Domain:** Data Analytics  
**Focus:** Public Service Request Analytics
