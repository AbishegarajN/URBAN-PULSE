
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="URBAN PULSE",
    page_icon="🏙️",
    layout="wide"
)


st.markdown("""
    <div class="dashboard-header">
        <div class="dashboard-title">🏙️ URBAN PULSE</div>
        <div class="dashboard-subtitle">
            NYC 311 Public Service Analytics Dashboard
        </div>
        <div class="dashboard-description">
            Explore public service requests, complaint patterns,
            agency workload and resolution performance across
            New York City's five boroughs.
        </div>
    </div>
""", unsafe_allow_html=True)

st.divider()


try:
    db = st.secrets["postgres"]

    connection_url = (
        f"postgresql+psycopg2://{db['username']}:"
        f"{db['password']}@{db['host']}:"
        f"{db['port']}/{db['database']}"
    )

    engine = create_engine(connection_url)

    with engine.connect() as connection:
        total_records = connection.execute(
            text("SELECT COUNT(*) FROM public.nyc_311")
        ).scalar()

    # Get complaint types from PostgreSQL
    with engine.connect() as connection:
        complaint_types = pd.read_sql(
            text("""
                SELECT DISTINCT complaint_type
                FROM public.nyc_311
                WHERE complaint_type IS NOT NULL
                ORDER BY complaint_type
            """),
            connection
        )["complaint_type"].tolist()

    st.subheader("🔎 Interactive Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        start_date = st.date_input(
            "Start Date",
            value=None,
            key="start_date"
        )

    with filter_col2:
        end_date = st.date_input(
            "End Date",
            value=None,
            key="end_date"
        )

    with filter_col3:
        selected_borough = st.selectbox(
            "Borough",
            options=[
                "All",
                "BROOKLYN",
                "QUEENS",
                "MANHATTAN",
                "BRONX",
                "STATEN ISLAND"
            ],
            index=0,
            key="selected_borough"
        )

    with filter_col4:
        selected_complaint = st.selectbox(
            "Complaint Type",
            options=["All"] + complaint_types,
            index=0,
            key="selected_complaint"
        )

    # INTERACTIVE FILTER OPTIONS

    with engine.connect() as connection:
        borough_options = pd.read_sql(
            text("""
                SELECT DISTINCT borough
                FROM public.nyc_311
                WHERE borough IS NOT NULL
                ORDER BY borough
            """),
            connection
        )["borough"].tolist()

        complaint_options = pd.read_sql(
            text("""
                SELECT DISTINCT complaint_type
                FROM public.nyc_311
                WHERE complaint_type IS NOT NULL
                ORDER BY complaint_type
            """),
            connection
        )["complaint_type"].tolist()

        date_limits = pd.read_sql(
            text("""
                SELECT
                    MIN(CAST(created_date AS TIMESTAMP)) AS min_date,
                    MAX(CAST(created_date AS TIMESTAMP)) AS max_date
                FROM public.nyc_311
                WHERE created_date IS NOT NULL
                  AND TRIM(created_date) <> ''
            """),
            connection
        )

    min_date = date_limits["min_date"].iloc[0].date()
    max_date = date_limits["max_date"].iloc[0].date()


    # FIVE MANDATORY DASHBOARD KPIs

        # BUILD DYNAMIC FILTER CONDITIONS
    conditions = []
    filter_params = {}

    if start_date:
        conditions.append("CAST(created_date AS DATE) >= :start_date")
        filter_params["start_date"] = start_date

    if end_date:
        conditions.append("CAST(created_date AS DATE) <= :end_date")
        filter_params["end_date"] = end_date

    if selected_borough != "All":
        conditions.append("borough = :borough")
        filter_params["borough"] = selected_borough

    if selected_complaint != "All":
        conditions.append("complaint_type = :complaint")
        filter_params["complaint"] = selected_complaint

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    
    with engine.connect() as connection:
        metrics = connection.execute(
            text(f"""
                SELECT
                    COUNT(DISTINCT unique_key) AS total_requests,

                    COUNT(*) FILTER (
                        WHERE is_closed = TRUE
                    ) AS closed_requests,

                    COUNT(*) FILTER (
                        WHERE is_closed = FALSE
                    ) AS open_requests,

                    PERCENTILE_CONT(0.5) WITHIN GROUP (
                        ORDER BY resolution_hours
                    ) FILTER (
                        WHERE resolution_hours IS NOT NULL
                        AND resolution_hours >= 0
                    ) AS median_resolution,

                    COUNT(*) FILTER (
                        WHERE resolution_hours > 72
                    ) AS over_72_hours,

                    COUNT(*) FILTER (
                        WHERE resolution_hours IS NOT NULL
                        AND resolution_hours >= 0
                    ) AS valid_resolution_count

                FROM public.nyc_311
                {where_clause}
                """), filter_params).mappings().one()


    total = metrics["total_requests"]
    closed = metrics["closed_requests"]
    open_count = metrics["open_requests"]

    median_resolution = metrics["median_resolution"]
    over_72 = metrics["over_72_hours"]
    valid_count = metrics["valid_resolution_count"]

    closure_rate = (
        closed / total * 100
        if total else 0
    )

    over_72_rate = (
        over_72 / valid_count * 100
        if valid_count else 0
    )

    # PROFESSIONAL KPI CARDS

    st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #202B3A;
        border: 1px solid #34445A;
        padding: 18px 20px;
        border-radius: 12px;
    }
    div[data-testid="stMetricLabel"] {
        color: #CBD5E1;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF;
        font-weight: 700;
    }

    .dashboard-header {
    background: linear-gradient(135deg, #202B3A, #34445A);
    padding: 28px 30px;
    border-radius: 14px;
    margin-bottom: 25px;
    border: 1px solid #34445A;
    }

    .dashboard-title {
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
    }

    .dashboard-subtitle {
        font-size: 20px;
        color: #CBD5E1;
        margin-top: 8px;
    }

    .dashboard-description {
        font-size: 15px;
        color: #CBD5E1;
        margin-top: 10px;
    }

    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("📊 Total Requests", f"{total:,}")

    col2.metric(
        "✅ Recorded Closure",
        f"{closure_rate:.2f}%"
    )

    col3.metric("📂 Open Requests", f"{open_count:,}")

    col4.metric(
        "⏱️ Median Resolution",
        f"{median_resolution:.2f} hrs"
        if median_resolution is not None else "N/A"
    )

    col5.metric(
        "⚠️ Over 72 Hours",
        f"{over_72_rate:.2f}%"
    )

    st.divider()


    st.subheader("1. Top 10 Complaint Categories")


    with engine.connect() as connection:
        category_data = pd.read_sql(
            text(f"""
                SELECT
                    complaint_type,
                    COUNT(*) AS total_complaints
                FROM public.nyc_311
                WHERE complaint_type IS NOT NULL
                AND TRIM(complaint_type) <> ''
                {"AND " + " AND ".join(conditions) if conditions else ""}
                GROUP BY complaint_type
                ORDER BY total_complaints DESC
                LIMIT 10
            """),
            connection,
            params=filter_params
        )


    category_data = category_data.sort_values(
        "total_complaints",
        ascending=True
    )

    st.bar_chart(
        category_data.set_index("complaint_type"),
        horizontal=True
    )


    st.divider()


    st.subheader("2. Agency Workload Distribution")


    with engine.connect() as connection:
        agency_data = pd.read_sql(
            text(f"""
                SELECT
                    agency,
                    COUNT(*) AS total_complaints
                FROM public.nyc_311
                WHERE agency IS NOT NULL
                  AND TRIM(agency) <> ''
                  {"AND " + " AND ".join(conditions) if conditions else ""}
                GROUP BY agency
                ORDER BY total_complaints DESC
                LIMIT 10
            """),
            connection,
            params=filter_params
        )



    if agency_data.empty:
        st.info("No agency data available.")
    else:
        st.bar_chart(
            agency_data.set_index("agency"),
            horizontal=True
        )

    
    # INVESTIGATION 3: REQUEST VOLUME BY BOROUGH

    st.divider()

    st.subheader("3. Request Volume by Borough")

    with engine.connect() as connection:
        borough_data = pd.read_sql(
            text(f"""
                SELECT
                    borough,
                    COUNT(DISTINCT unique_key) AS total_requests
                FROM public.nyc_311
                WHERE borough IS NOT NULL
                  AND UPPER(TRIM(borough)) NOT IN ('UNSPECIFIED', '')
                  {"AND " + " AND ".join(conditions) if conditions else ""}
                GROUP BY borough
                ORDER BY total_requests DESC
            """),
            connection,
            params=filter_params
        )
    if not borough_data.empty:


        chart_data = borough_data.set_index("borough")

        st.bar_chart(
            chart_data,
            horizontal=True
        )

    else:
        st.warning("No borough data available.")

    
    # INVESTIGATION 4: DEMAND BY WEEKDAY AND HOUR

    st.divider()

    st.subheader("4. Demand by Weekday and Hour")

    with engine.connect() as connection:

        demand_data = pd.read_sql(
            text("""
                SELECT
                    INITCAP(TRIM(created_weekday)) AS weekday,
                    TRIM(created_hour::text)::int AS hour,
                    COUNT(DISTINCT unique_key) AS total_requests
                FROM public.nyc_311
                WHERE created_weekday IS NOT NULL
                AND UPPER(TRIM(created_weekday)) IN (
                    'MONDAY', 'TUESDAY', 'WEDNESDAY',
                    'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'
                )
                AND created_hour::text ~ '^[0-9]{1,2}$'
                AND TRIM(created_hour::text)::int BETWEEN 0 AND 23
                GROUP BY 1, 2
                ORDER BY 1, 2
            """),
            connection
        )

    if not demand_data.empty:


        # 4. DEMAND BY WEEKDAY AND HOUR

        weekday_hour_data = pd.read_sql(
    text("""
        SELECT
            created_weekday,
            created_hour,
            COUNT(DISTINCT unique_key) AS total_complaints
        FROM public.nyc_311
        WHERE created_weekday IS NOT NULL
          AND created_hour IS NOT NULL
        GROUP BY created_weekday, created_hour
    """),
    engine
)

        st.subheader("Demand Heatmap: Weekday vs Hour")

        weekday_order = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        heatmap_data = weekday_hour_data.pivot(
            index="created_weekday",
            columns="created_hour",
            values="total_complaints"
        )

        heatmap_data = heatmap_data.reindex(weekday_order)
        heatmap_data = heatmap_data.reindex(columns=range(24), fill_value=0)



       
        # Prepare numeric heatmap values
        heatmap_values = heatmap_data.astype(float).to_numpy()

        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_values,
                x=list(range(24)),
                y=weekday_order,
                colorscale="YlOrRd",
                zmin=0,
                zmax=heatmap_values.max(),
                colorbar=dict(
                    title="Total Complaints"
                ),
                text=heatmap_values,
                texttemplate="%{text:.0f}",
                hovertemplate=
                "Weekday: %{y}<br>" +
                "Hour: %{x}<br>" +
                "Complaints: %{z}<extra></extra>"
            )
        )
        fig.update_layout(
            showlegend=False
        )

        fig.update_layout(
            title="NYC 311 Demand by Weekday and Hour",
            height=650,
            template="plotly_dark",
            paper_bgcolor="#111111",
            plot_bgcolor="#111111",
            font=dict(color="white"),
            xaxis=dict(
                title="Hour of Day",
                tickmode="linear",
                dtick=1
            ),
            yaxis=dict(
                title="Weekday",
                autorange="reversed"
            )
        )
        fig.update_traces(showlegend=False)
        fig.update_layout(showlegend=False)
        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # 5. RECORDED REQUEST STATUS DISTRIBUTION

        st.divider()
        st.header("5. Recorded Request Status Distribution")

        st.subheader("Request Status Overview")

        status_query = f"""
            SELECT
                status,
                COUNT(*) AS total_requests
            FROM public.nyc_311
            WHERE 1=1
            {"AND " + " AND ".join(conditions) if conditions else ""}
            GROUP BY status
            ORDER BY total_requests DESC;
        """

        with engine.connect() as connection:
            status_data = pd.read_sql(
                text(status_query),
                connection,
                params=filter_params
            )

        fig = px.pie(
            status_data,
            names="status",
            values="total_requests",
            hole=0.45,
            title="NYC 311 Request Status Distribution"
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label"
        )

        fig.update_layout(
            template="plotly_dark",
            height=550
        )

        st.plotly_chart(fig, use_container_width=True)

        # Create weekday-hour pivot table

        weekdays = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        heatmap_data = demand_data.pivot_table(
            index="weekday",
            columns="hour",
            values="total_requests",
            aggfunc="sum",
            fill_value=0
        )

        heatmap_data = heatmap_data.reindex(
            index=weekdays,
            columns=range(24),
            fill_value=0
        )

        # Display heatmap

        fig, ax = plt.subplots(figsize=(14, 6))

        image = ax.imshow(
            heatmap_data,
            aspect="auto",
            cmap="YlOrRd",
            interpolation="nearest"
        )

        ax.set_title("NYC 311 Request Demand by Weekday and Hour")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Weekday")

        ax.set_xticks(range(24))
        ax.set_xticklabels(range(24))

        ax.set_yticks(range(7))
        ax.set_yticklabels(weekdays)

        fig.colorbar(
            image,
            ax=ax,
            label="Total Service Requests"
        )

        plt.tight_layout()

        plt.close(fig)

    else:
        st.warning("No weekday and hourly demand data available.")


    # 6. Descriptive Statistics of Resolution Durations

    st.header("6. Descriptive Statistics of Resolution Durations")


    resolution_stats_query = f"""
        SELECT
            COUNT(*) AS total_closed_requests,
            ROUND(AVG(resolution_hours)::numeric, 2) AS mean_hours,
            ROUND(
                PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY resolution_hours)::numeric, 2
            ) AS median_hours,
            ROUND(STDDEV(resolution_hours)::numeric, 2) AS std_deviation,
            ROUND(MIN(resolution_hours)::numeric, 2) AS minimum_hours,
            ROUND(
                PERCENTILE_CONT(0.25)
                WITHIN GROUP (ORDER BY resolution_hours)::numeric, 2
            ) AS q1_hours,
            ROUND(
                PERCENTILE_CONT(0.75)
                WITHIN GROUP (ORDER BY resolution_hours)::numeric, 2
            ) AS q3_hours,
            ROUND(MAX(resolution_hours)::numeric, 2) AS maximum_hours
        FROM public.nyc_311
        WHERE resolution_hours IS NOT NULL
          AND resolution_hours >= 0
          {"AND " + " AND ".join(conditions) if conditions else ""}
    """


    with engine.connect() as connection:
        resolution_stats = pd.read_sql(
            text(resolution_stats_query),
            connection,
            params=filter_params
        )

    st.subheader("Resolution Duration Statistical Summary")

    st.dataframe(resolution_stats, use_container_width=True)

    # 7. MEDIAN RESOLUTION BY COMPLAINT CATEGORY

    st.divider()
    st.header("7. Median Resolution by Complaint Category")

    category_resolution_query = f"""
            SELECT
                complaint_type,
                COUNT(*) AS total_requests,
                ROUND(
                    PERCENTILE_CONT(0.5)
                    WITHIN GROUP (ORDER BY resolution_hours)::numeric,
                    2
                ) AS median_resolution_hours
            FROM public.nyc_311
            WHERE complaint_type IS NOT NULL
              AND resolution_hours IS NOT NULL
              AND resolution_hours >= 0
              {"AND " + " AND ".join(conditions) if conditions else ""}
            GROUP BY complaint_type
            ORDER BY median_resolution_hours DESC;
        """

    with engine.connect() as connection:
        category_resolution_data = pd.read_sql(
            text(category_resolution_query),
            connection,
            params=filter_params
        )

        st.subheader("Median Resolution Time by Complaint Category")

        fig = px.bar(
            category_resolution_data.head(15),
            x="median_resolution_hours",
            y="complaint_type",
            orientation="h",
            color="median_resolution_hours",
            title="Top 15 Complaint Categories by Median Resolution Time",
            labels={
                "median_resolution_hours": "Median Resolution Time (Hours)",
                "complaint_type": "Complaint Category"
            }
        )

        fig.update_layout(
            template="plotly_dark",
            height=650,
            yaxis={"categoryorder": "total ascending"},
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)


        # 8. MEDIAN RESOLUTION BY AGENCY

        st.divider()
        st.header("8. Median Resolution by Agency")

        agency_resolution_query = f"""
            SELECT
                agency,
                COUNT(*) AS total_requests,
                ROUND(
                    PERCENTILE_CONT(0.5)
                    WITHIN GROUP (ORDER BY resolution_hours)::numeric,
                    2
                ) AS median_resolution_hours
            FROM public.nyc_311
            WHERE agency IS NOT NULL
              AND resolution_hours IS NOT NULL
              AND resolution_hours >= 0
              {"AND " + " AND ".join(conditions) if conditions else ""}
            GROUP BY agency
            ORDER BY median_resolution_hours DESC;
        """

        with engine.connect() as connection:
            agency_resolution_data = pd.read_sql(
            text(agency_resolution_query),
            connection,
            params=filter_params
        )

        st.subheader("Median Resolution Time by Agency")

        fig = px.bar(
            agency_resolution_data,
            x="median_resolution_hours",
            y="agency",
            orientation="h",
            color="median_resolution_hours",
            title="Median Resolution Time Across Agencies",
            labels={
                "median_resolution_hours": "Median Resolution Time (Hours)",
                "agency": "Agency"
            }
        )

        fig.update_layout(
            template="plotly_dark",
            height=650,
            yaxis={"categoryorder": "total ascending"},
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # 9. IQR-BASED OUTLIER INVESTIGATION

        st.divider()
        st.header("9. IQR-Based Outlier Investigation")

        outlier_query = f"""
            SELECT resolution_hours
            FROM public.nyc_311
            WHERE resolution_hours IS NOT NULL
              AND resolution_hours >= 0
              {"AND " + " AND ".join(conditions) if conditions else ""}
        """

        with engine.connect() as connection:
            outlier_data = pd.read_sql(
                text(outlier_query),
                connection,
                params=filter_params
            )

        # Calculate IQR statistics

        q1 = outlier_data["resolution_hours"].quantile(0.25)
        q3 = outlier_data["resolution_hours"].quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        st.subheader("IQR Statistical Summary")

        st.write(f"Q1 (25th Percentile): {q1:.2f} hours")
        st.write(f"Q3 (75th Percentile): {q3:.2f} hours")
        st.write(f"IQR: {iqr:.2f} hours")
        st.write(f"Lower Bound: {lower_bound:.2f} hours")
        st.write(f"Upper Bound: {upper_bound:.2f} hours")

        outlier_count = (
            (outlier_data["resolution_hours"] < lower_bound) |
            (outlier_data["resolution_hours"] > upper_bound)
        ).sum()

        st.write(f"Total Outliers: {outlier_count}")

        st.subheader("Resolution Time Outlier Box Plot")

        fig = px.box(
            outlier_data,
            y="resolution_hours",
            title="IQR-Based Outlier Detection",
            points="outliers",
            labels={
                "resolution_hours": "Resolution Time (Hours)"
            }
        )

        fig.add_hline(
            y=upper_bound,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Upper Bound: {upper_bound:.2f} hours"
        )

        fig.update_layout(
            template="plotly_dark",
            height=600,
            yaxis_title="Resolution Time (Hours)"
        )

        st.plotly_chart(fig, use_container_width=True)


    
        # 10. RESOLUTION-TIME SKEWNESS AND DISTRIBUTION

        st.divider()
        st.header("10. Resolution-Time Skewness and Distribution")

        st.subheader("Resolution Time Distribution")

        skewness_query = f"""
            SELECT
                resolution_hours
            FROM public.nyc_311
            WHERE resolution_hours IS NOT NULL
              AND resolution_hours >= 0
              {"AND " + " AND ".join(conditions) if conditions else ""}
        """

        with engine.connect() as connection:
            skewness_data = pd.read_sql(
                text(skewness_query),
                connection,
                params=filter_params
            )

        # Calculate skewness
        skewness_value = skewness_data["resolution_hours"].skew()

        st.metric(
            "Resolution-Time Skewness",
            round(skewness_value, 3)
        )

        # Create histogram
        fig = px.histogram(
            skewness_data,
            x="resolution_hours",
            nbins=50,
            title="Distribution of NYC 311 Resolution Times",
            labels={
                "resolution_hours": "Resolution Time (Hours)",
                "count": "Number of Requests"
            }
        )

        fig.update_layout(
            template="plotly_dark",
            height=550
        )

        st.plotly_chart(fig, use_container_width=True)



        # 11. GEOGRAPHIC COMPLAINT CONCENTRATION

        st.divider()
        st.header("11. Geographic Complaint Concentration")

        st.subheader("Complaint Volume by Borough")

        borough_query = f"""
            SELECT
                borough,
                COUNT(*) AS total_complaints
            FROM public.nyc_311
            WHERE borough IS NOT NULL
            AND TRIM(borough) <> ''
            AND borough <> 'UNSPECIFIED'
            {"AND " + " AND ".join(conditions) if conditions else ""}
            GROUP BY borough
            ORDER BY total_complaints DESC;
        """

        with engine.connect() as connection:
            borough_data = pd.read_sql(
                text(borough_query),
                connection,
                params=filter_params
            )

        
        fig = px.bar(
            borough_data[
                borough_data["borough"] != "UNSPECIFIED"
            ],
            x="total_complaints",
            y="borough",
            orientation="h",
            title="NYC 311 Complaints by Borough",
            text="total_complaints"
        )

        fig.update_layout(
            template="plotly_dark",
            height=500,
            xaxis_title="Total Complaints",
            yaxis_title="Borough",
            yaxis=dict(autorange="reversed")
        )

        st.plotly_chart(fig, use_container_width=True)

                # MEDIAN RESOLUTION TIME BY BOROUGH

        st.subheader("Median Resolution Time by Borough")

        borough_resolution_query = f"""
            SELECT
                borough,
                COUNT(*) AS resolved_requests,
                ROUND(
                    PERCENTILE_CONT(0.5)
                    WITHIN GROUP (ORDER BY resolution_hours)::numeric,
                    2
                ) AS median_resolution_hours
            FROM public.nyc_311
            WHERE borough IS NOT NULL
              AND TRIM(borough) <> ''
              AND UPPER(TRIM(borough)) <> 'UNSPECIFIED'
              AND resolution_hours IS NOT NULL
              AND resolution_hours >= 0
              {"AND " + " AND ".join(conditions) if conditions else ""}
            GROUP BY borough
            ORDER BY median_resolution_hours DESC;
        """

        with engine.connect() as connection:
            borough_resolution_data = pd.read_sql(
                text(borough_resolution_query),
                connection,
                params=filter_params
            )

        if not borough_resolution_data.empty:

            fig = px.bar(
                borough_resolution_data,
                x="median_resolution_hours",
                y="borough",
                orientation="h",
                text="median_resolution_hours",
                title="Median Complaint Resolution Time by Borough",
                labels={
                    "median_resolution_hours": "Median Resolution (Hours)",
                    "borough": "Borough"
                }
            )

            fig.update_layout(
                template="plotly_dark",
                height=450,
                yaxis=dict(autorange="reversed")
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No resolution data available for the selected filters.")


        # 12. RECORDED CLOSURE-RATE COMPARISON

        st.divider()
        st.header("12. Recorded Closure-Rate Comparison")

        st.subheader("Closure Rate by Borough")


        closure_rate_query = f"""
            SELECT
                borough,
                COUNT(*) AS total_requests,
                COUNT(*) FILTER (
                    WHERE is_closed = TRUE
                ) AS closed_requests,
                ROUND(
                    COUNT(*) FILTER (
                        WHERE is_closed = TRUE
                    ) * 100.0 / NULLIF(COUNT(*), 0),
                    2
                ) AS closure_rate
            FROM public.nyc_311
            WHERE borough IS NOT NULL
              AND TRIM(borough) <> ''
              AND UPPER(TRIM(borough)) <> 'UNSPECIFIED'
              {"AND " + " AND ".join(conditions) if conditions else ""}
            GROUP BY borough
            ORDER BY closure_rate DESC;
        """


        with engine.connect() as connection:
            closure_data = pd.read_sql(
                text(closure_rate_query),
                connection,
                params=filter_params
            )


    if not closure_data.empty:

        fig = px.bar(
            closure_data,
            x="borough",
            y="closure_rate",
            text="closure_rate",
            title="NYC 311 Closure Rate by Borough",
            labels={
                "borough": "Borough",
                "closure_rate": "Closure Rate (%)"
            }
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig.update_layout(
            template="plotly_dark",
            height=500,
            yaxis_title="Closure Rate (%)",
            xaxis_title="Borough",
            yaxis=dict(range=[0, 100])
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No closure-rate data available for the selected filters.")

    # 13. High-Volume Categories with Long Resolution Times

    st.header("13. High-Volume Categories with Long Resolution Times")


    category_performance_query = f"""
        SELECT
            complaint_type,
            COUNT(*) AS total_requests,
            ROUND(
                PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY resolution_hours)::numeric,
                2
            ) AS median_resolution_hours
        FROM public.nyc_311
        WHERE complaint_type IS NOT NULL
          AND resolution_hours IS NOT NULL
          AND resolution_hours >= 0
          {"AND " + " AND ".join(conditions) if conditions else ""}
        GROUP BY complaint_type
        HAVING COUNT(*) >= 100
        ORDER BY total_requests DESC
        LIMIT 30;
    """

    with engine.connect() as connection:
        category_performance = pd.read_sql(
            text(category_performance_query),
            connection,
            params=filter_params
        )


    if not category_performance.empty:

        category_performance["total_requests"] = pd.to_numeric(
            category_performance["total_requests"],
            errors="coerce"
        )

        category_performance["median_resolution_hours"] = pd.to_numeric(
            category_performance["median_resolution_hours"],
            errors="coerce"
        )

        fig = px.scatter(
            category_performance,
            x="total_requests",
            y="median_resolution_hours",
            size="total_requests",
            color="complaint_type",
            hover_name="complaint_type",
            title="High-Volume Categories with Long Resolution Times"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No complaint data available for the selected filters.")

except Exception as e:
    st.error("Database connection failed.")
    st.exception(e)
