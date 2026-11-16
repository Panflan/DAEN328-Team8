
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy import inspect

st.set_page_config(
    page_title="NYC 311 Service Requests",
    page_icon="🏙️",
    layout="wide"
)

load_dotenv()

# Database connection
db_user = os.getenv("PSQL_USER")
db_password = os.getenv("PSQL_PASSWORD")
db_name = os.getenv("PSQL_DB")

engine = None

if all([db_user, db_password, db_name]):
    DB_URL = URL.create(
        "postgresql+psycopg2",
        username=db_user,
        password=db_password,
        host="127.0.0.1",
        port=5433,
        database=db_name
    )
    engine = create_engine(DB_URL)

# Dashboard title
st.title("🏙️ NYC 311 Service Requests Dashboard")

st.markdown("""
Explore patterns in New York City's 311 service requests,
including complaint types, boroughs, agencies, and resolution times.
""")

st.divider()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

borough = st.sidebar.selectbox(
    "Select Borough",
    [
        "All Boroughs",
        "BRONX",
        "BROOKLYN",
        "MANHATTAN",
        "QUEENS",
        "STATEN ISLAND"
    ]
)

year = st.sidebar.selectbox(
    "Select Year",
    ["All Years", "2020", "2021", "2022", "2023",
     "2024", "2025", "2026"]
)

# Build filters safely
filters = []
params = {}

if borough != "All Boroughs":
    filters.append("l.borough = :borough")
    params["borough"] = borough

if year != "All Years":
    filters.append("EXTRACT(YEAR FROM sr.created_date) = :year")
    params["year"] = int(year)

where_clause = ""
if filters:
    where_clause = "WHERE " + " AND ".join(filters)


# Database query helper
def run_query(query):
    with engine.connect() as connection:
        return pd.read_sql_query(
            text(query),
            connection,
            params=params
        )


# Check database connection and tables
if engine is None:
    st.error("Database connection is not configured.")
    st.stop()

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    required_tables = [
        "service_requests",
        "complaint_types",
        "agencies",
        "locations"
    ]

    existing_tables = inspect(engine).get_table_names()

    missing_tables = [
        table for table in required_tables
        if table not in existing_tables
    ]

    if missing_tables:
        st.warning(
            "The database is connected, but the required tables "
            "have not been created yet: " + ", ".join(missing_tables)
        )
        st.info(
            "Once the ETL pipeline creates the tables and loads "
            "NYC 311 records, the dashboard will display real data."
        )
        st.stop()

    st.success("Successfully connected to PostgreSQL!")

except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


# Dashboard filters
st.write(f"**Selected Borough:** {borough}")
st.write(f"**Selected Year:** {year}")

st.divider()


# SQL queries
metrics_query = f"""
SELECT
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (
        WHERE sr.closed_date IS NOT NULL
    ) AS closed_requests
FROM service_requests sr
LEFT JOIN locations l ON sr.location_id = l.location_id
{where_clause};
"""

complaint_query = f"""
SELECT
    ct.complaint_type,
    COUNT(*) AS request_count
FROM service_requests sr
JOIN complaint_types ct
    ON sr.complaint_type_id = ct.complaint_type_id
LEFT JOIN locations l
    ON sr.location_id = l.location_id
{where_clause}
GROUP BY ct.complaint_type
ORDER BY request_count DESC
LIMIT 10;
"""

monthly_query = f"""
SELECT
    DATE_TRUNC('month', sr.created_date) AS month,
    COUNT(*) AS request_count
FROM service_requests sr
LEFT JOIN locations l
    ON sr.location_id = l.location_id
{where_clause}
GROUP BY month
ORDER BY month;
"""

borough_query = f"""
SELECT
    l.borough,
    COUNT(*) AS request_count
FROM service_requests sr
JOIN locations l
    ON sr.location_id = l.location_id
{where_clause}
GROUP BY l.borough
ORDER BY request_count DESC;
"""

agency_query = f"""
SELECT
    a.agency_name,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (
        WHERE sr.closed_date IS NOT NULL
    ) AS closed_requests
FROM service_requests sr
JOIN agencies a
    ON sr.agency_id = a.agency_id
LEFT JOIN locations l
    ON sr.location_id = l.location_id
{where_clause}
GROUP BY a.agency_name
ORDER BY total_requests DESC
LIMIT 10;
"""

resolution_query = f"""
SELECT
    ct.complaint_type,
    AVG(
        EXTRACT(EPOCH FROM (
            sr.closed_date - sr.created_date
        )) / 86400
    ) AS average_days
FROM service_requests sr
JOIN complaint_types ct
    ON sr.complaint_type_id = ct.complaint_type_id
LEFT JOIN locations l
    ON sr.location_id = l.location_id
{where_clause}
AND sr.closed_date IS NOT NULL
AND sr.closed_date >= sr.created_date
GROUP BY ct.complaint_type
ORDER BY average_days DESC
LIMIT 10;
"""


# Load real database data
try:
    metrics_data = run_query(metrics_query)
    complaint_data = run_query(complaint_query)
    monthly_data = run_query(monthly_query)
    borough_data = run_query(borough_query)
    agency_data = run_query(agency_query)
    resolution_data = run_query(resolution_query)

except Exception as e:
    st.error(f"Could not load dashboard data: {e}")
    st.stop()


# Overview metrics
st.subheader("Overview")

total_requests = int(metrics_data.iloc[0]["total_requests"])
closed_requests = int(metrics_data.iloc[0]["closed_requests"])

most_common = (
    complaint_data.iloc[0]["complaint_type"]
    if not complaint_data.empty else "No data"
)

top_borough = (
    borough_data.iloc[0]["borough"]
    if not borough_data.empty else "No data"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Requests", f"{total_requests:,}")
col2.metric("Most Common Complaint", most_common)
col3.metric("Top Borough", top_borough)
col4.metric("Closed Requests", f"{closed_requests:,}")

st.divider()


# Complaint analysis
st.subheader("Complaint Analysis")

st.write("**1. Most Common Complaint Types**")

if not complaint_data.empty:
    complaint_data = complaint_data.rename(columns={
        "complaint_type": "Complaint Type",
        "request_count": "Number of Requests"
    })

    st.bar_chart(
        complaint_data,
        x="Complaint Type",
        y="Number of Requests"
    )
else:
    st.info("No complaint data available for these filters.")


st.write("**2. Service Requests Over Time**")

if not monthly_data.empty:
    monthly_data = monthly_data.rename(columns={
        "month": "Month",
        "request_count": "Number of Requests"
    })

    st.line_chart(
        monthly_data,
        x="Month",
        y="Number of Requests"
    )
else:
    st.info("No monthly data available for these filters.")


st.write("**3. Service Requests by Borough**")

if not borough_data.empty:
    borough_chart = borough_data.rename(columns={
        "borough": "Borough",
        "request_count": "Number of Requests"
    })

    st.bar_chart(
        borough_chart,
        x="Borough",
        y="Number of Requests"
    )
else:
    st.info("No borough data available for these filters.")


st.divider()


# Agency performance
st.subheader("Agency Performance")

st.write("**4. Requests by Agency and Closure Status**")

if not agency_data.empty:
    agency_chart = agency_data.rename(columns={
        "agency_name": "Agency",
        "total_requests": "Total Requests",
        "closed_requests": "Closed Requests"
    })

    st.bar_chart(
        agency_chart.set_index("Agency")
    )
else:
    st.info("No agency data available for these filters.")


# Resolution analysis
st.subheader("Resolution Analysis")

st.write("**5. Average Resolution Time by Complaint Type**")

if not resolution_data.empty:
    resolution_chart = resolution_data.rename(columns={
        "complaint_type": "Complaint Type",
        "average_days": "Average Days to Resolve"
    })

    st.bar_chart(
        resolution_chart.set_index("Complaint Type"),
        horizontal=True
    )
else:
    st.info("No resolution data available for these filters.")
