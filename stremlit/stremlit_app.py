import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Flask API URL
FLASK_API_URL = "http://127.0.0.1:2424/global-json-info"



# import time

# # Add these at the top with other constants
# TOKEN_EXPIRATION = 3000  # 1 hour in seconds
# MAX_REQUESTS_PER_MINUTE = 20  # Rate limiting

# def fetch_data():
#     session = requests.Session()
#     login_url = "http://127.0.0.1:2424/login"
#     credentials = {"username": "rokon", "password": "rokon"}
    
#     # Track request count and last request time
#     if not hasattr(fetch_data, "request_count"):
#         fetch_data.request_count = 0
#     if not hasattr(fetch_data, "last_request_time"):
#         fetch_data.last_request_time = time.time()
    
#     # Check rate limit
#     current_time = time.time()
#     if current_time - fetch_data.last_request_time < 60:  # 1 minute window
#         if fetch_data.request_count >= MAX_REQUESTS_PER_MINUTE:
#             st.error("Rate limit exceeded. Please try again later.")
#             return None
#     else:
#         # Reset counter if more than 1 minute has passed
#         fetch_data.request_count = 0
#         fetch_data.last_request_time = current_time

#     # Generate or renew token
#     if not hasattr(fetch_data, "token") or (current_time - getattr(fetch_data, "token_timestamp", 0)) > TOKEN_EXPIRATION:
#         # Request new token
#         response = session.post(login_url, json=credentials)
#         if response.status_code != 200:
#             st.error("Login failed. Please check your credentials.")
#             return None
        
#         # Extract token from response
#         try:
#             fetch_data.token = response.json().get("access_token")
#             fetch_data.token_timestamp = current_time
#         except Exception as e:
#             st.error(f"Token extraction failed: {str(e)}")
#             return None

#     # Make authenticated request
#     headers = {
#         "Authorization": f"Bearer {fetch_data.token}",
#         "Content-Type": "application/json"
#     }
    
#     try:
#         response = session.get(FLASK_API_URL, headers=headers)
#         fetch_data.request_count += 1
        
#         if response.status_code == 200:
#             return response.json()
#         elif response.status_code == 401:
#             st.error("Token expired. Renewing...")
#             del fetch_data.token 
#             return fetch_data() 
#         elif response.status_code == 429:
#             st.error("API rate limit exceeded. Please wait...")
#             return None
#         else:
#             st.error(f"API request failed: {response.status_code}")
#             return None
            
#     except Exception as e:
#         st.error(f"Request failed: {str(e)}")
#         return None
    


def fetch_data():
    session = requests.Session()
    login_url = "http://127.0.0.1:2424/login"
    credentials = {"username": "rokon", "password": "rokon"}
    
    response = session.post(login_url, data=credentials)
    if response.status_code != 200:
        st.error("Login failed. Please check your credentials.")
        return None

    response = session.get(FLASK_API_URL)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 302:
        st.error("API is redirecting to login. Authentication required.")
    else:
        st.error(f"Unexpected error: {response.status_code}")
    return None




def clean_text(value):
    return str(value).encode('utf-8', 'ignore').decode('utf-8')

# Load data
st.set_page_config(page_title="Hotel Data Dashboard", layout="wide")
st.title("📊 Professional Hotel Data Dashboard")
data = fetch_data()

if data:
    # Global Overview Metrics
    st.subheader("Global Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Vervotech IDs", clean_text(data.get("total_vervotech_id", "N/A")))
    col2.metric("Total Giata IDs", clean_text(data.get("total_giata_id", "N/A")))
    col3.metric("Last Update", clean_text(data.get("get_last_update_data", "N/A")))
    col4.metric("Created At", clean_text(data.get("created_at", "N/A")))

    # Update Information Visualization
    st.subheader("Update Performance Metrics")
    update_info = data.get("update_info", {})
    if update_info:
        # Convert string numbers to integers
        update_metrics = {
            'New Data': {
                'Success': int(update_info.get("find_new_data_success", 0)),
                'Skipped': int(update_info.get("find_new_data_skipping", 0))
            },
            'Update Data': {
                'Success': int(update_info.get("find_update_data_success", 0)),
                'Skipped': int(update_info.get("find_update_data_skipping", 0))
            }
        }
        
        df_update = pd.DataFrame([
            {'Category': 'New Data', 'Type': 'Success', 'Count': update_metrics['New Data']['Success']},
            {'Category': 'New Data', 'Type': 'Skipped', 'Count': update_metrics['New Data']['Skipped']},
            {'Category': 'Update Data', 'Type': 'Success', 'Count': update_metrics['Update Data']['Success']},
            {'Category': 'Update Data', 'Type': 'Skipped', 'Count': update_metrics['Update Data']['Skipped']}
        ])

        fig_update = px.bar(df_update, x='Category', y='Count', color='Type', 
                           barmode='group', title="Data Update Performance",
                           labels={'Count': 'Number of Operations'},
                           color_discrete_map={'Success': '#2ca02c', 'Skipped': '#d62728'})
        st.plotly_chart(fig_update, use_container_width=True)
    else:
        st.warning("No update information available.")

    # Supplier Comparison Section
    st.subheader("Supplier Comparison")
    supplier_total = data.get("supplier_hotel_total_data_count", {})
    supplier_updates = data.get("supplier_hotel_update_info", {})
    
    if supplier_total and supplier_updates:
        # Create combined DataFrame
        df_combined = pd.DataFrame([
            {
                'Supplier': supplier,
                'Total Hotels': int(total),
                'Recent Updates': int(supplier_updates.get(supplier, 0))
            }
            for supplier, total in supplier_total.items()
            if int(total) > 0  # Filter out suppliers with 0 hotels
        ])
        
        # Sort by Total Hotels descending
        df_combined = df_combined.sort_values('Total Hotels', ascending=False)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Total Hotels", "Recent Updates", "Combined View"])
        
        with tab1:
            fig_total = px.bar(df_combined, x='Supplier', y='Total Hotels', 
                              title="Total Hotels per Supplier",
                              color='Total Hotels',
                              color_continuous_scale='Blues')
            st.plotly_chart(fig_total, use_container_width=True)
        
        with tab2:
            fig_updates = px.bar(df_combined, x='Supplier', y='Recent Updates',
                               title="Recent Updates per Supplier",
                               color='Recent Updates',
                               color_continuous_scale='Greens')
            st.plotly_chart(fig_updates, use_container_width=True)
        
        with tab3:
            fig_combined = px.bar(df_combined, x='Supplier', y=['Total Hotels', 'Recent Updates'],
                                title="Supplier Comparison: Total vs Updates",
                                barmode='group',
                                labels={'value': 'Count', 'variable': 'Metric'},
                                color_discrete_map={'Total Hotels': '#1f77b4', 'Recent Updates': '#2ca02c'})
            st.plotly_chart(fig_combined, use_container_width=True)
    else:
        st.warning("Supplier data not available for comparison.")

    # Global Table Visualization
    st.subheader("Global Table Statistics")
    global_table = data.get("global_table", {})
    if global_table:
        # Filter out non-numeric values and convert to integers
        gt_data = {k: int(v) for k, v in global_table.items() if v.isdigit()}
        df_global = pd.DataFrame(list(gt_data.items()), columns=['Metric', 'Value'])
        
        # Create columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            fig_global = px.bar(df_global, x='Metric', y='Value', 
                              title="Global Table Metrics",
                              color='Metric',
                              text='Value',
                              color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_global.update_traces(textposition='outside')
            st.plotly_chart(fig_global, use_container_width=True)
        
        with col2:
            st.markdown("**Global Table Details**")
            st.markdown(f"""
                - Last Data Addition: {global_table.get('new_data_add_time', 'N/A')}
                - Total Entries: {global_table.get('total_global_table_id', 'N/A')}
                - New Content Updates: {global_table.get('new_content_update', 'N/A')}
            """)
    else:
        st.warning("No global table data available.")

# Time Series Analysis
st.subheader("📅 Update Timeline Analysis")
try:
    # Handle different date formats
    created_at = data.get('created_at', '').split(' GMT')[0].strip()
    last_update = data.get('get_last_update_data', '').strip()
    
    # Convert using appropriate formats
    update_dates = pd.DataFrame({
        'Event': ['Data Creation', 'Last Update'],
        'Start': [
            pd.to_datetime(created_at, format='%a, %d %b %Y %H:%M:%S'),
            pd.to_datetime(last_update, format='%Y-%m-%d')
        ],
        'Finish': [
            pd.to_datetime(created_at, format='%a, %d %b %Y %H:%M:%S') + pd.Timedelta(hours=1),
            pd.to_datetime(last_update, format='%Y-%m-%d') + pd.Timedelta(hours=1)
        ],
        'Description': [
            f"Initial data creation at {created_at}",
            f"Last update performed on {last_update}"
        ]
    })
    
    # Create timeline with enhanced styling
    fig_timeline = px.timeline(
        update_dates, 
        x_start="Start", 
        x_end="Finish", 
        y="Event",
        title="📅 Data Timeline Overview",
        color="Event",
        color_discrete_sequence=['#636EFA', '#EF553B'],  # Custom colors
        hover_name="Event",
        hover_data={"Description": True, "Start": "|%B %d, %Y %I:%M %p"},
        labels={"Start": "Timeline", "Event": "Milestone"}
    )
    
    # Add markers with custom styling
    for i, row in update_dates.iterrows():
        fig_timeline.add_scatter(
            x=[row['Start']],
            y=[row['Event']],
            mode='markers+text',
            marker=dict(
                size=18,
                color=px.colors.qualitative.Pastel[i],
                line=dict(width=2, color='DarkSlateGrey')
            ),
            text=["★"],  # Star symbol as marker
            textposition="middle right",
            textfont=dict(size=14, color='black'),
            name=f"{row['Event']} Marker",
            showlegend=False
        )
    
    # Enhanced layout and styling
    fig_timeline.update_layout(
        title_font=dict(size=24, color='#2a3f5f', family="Arial"),
        xaxis_title="Timeline",
        yaxis_title="Milestone",
        showlegend=True,
        hovermode="x unified",
        plot_bgcolor='rgba(245,245,245,1)',
        paper_bgcolor='rgba(255,255,255,1)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial"
        )
    )
    
    # Customize x-axis with better date formatting
    fig_timeline.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(step="all", label="All")
            ]),
            bgcolor='#F0F2F6',
            activecolor='#636EFA',
            bordercolor='#D3D3D3'
        ),
        tickformat="%b %d, %Y\n%I:%M %p",
        gridcolor='#D3D3D3',
        zerolinecolor='#D3D3D3'
    )
    
    # Customize y-axis
    fig_timeline.update_yaxes(
        tickfont=dict(size=14, color='#2a3f5f'),
        gridcolor='#D3D3D3'
    )
    
    # Add annotations for better context
    fig_timeline.add_annotation(
        x=update_dates['Start'].min(),
        y=1.1,
        text="Timeline shows key data milestones",
        showarrow=False,
        font=dict(size=12, color='gray')
    )
    
    # Display the chart
    st.plotly_chart(fig_timeline, use_container_width=True)
    
except Exception as e:
    st.warning(f"Could not display timeline: {str(e)}")
    st.error(f"Raw date values: Created At - {data.get('created_at')}, Last Update - {data.get('get_last_update_data')}")





# Supplier Activity Analysis
st.subheader("📈 Supplier Activity Correlation")
try:
    if supplier_total and supplier_updates:
        # Create analysis dataframe
        df_activity = pd.DataFrame([
            {
                'Supplier': supplier,
                'Total Hotels': int(total),
                'Recent Updates': int(supplier_updates.get(supplier, 0)),
                'Update Ratio': int(supplier_updates.get(supplier, 0)) / int(total) if int(total) > 0 else 0
            }
            for supplier, total in supplier_total.items()
            if int(total) > 0  # Exclude suppliers with no hotels
        ])
        
        # Create interactive scatter plot
        fig_activity = px.scatter(
            df_activity,
            x='Total Hotels',
            y='Recent Updates',
            size='Total Hotels',
            color='Supplier',
            hover_name='Supplier',
            title='Supplier Activity Correlation: Size vs Updates',
            labels={
                'Total Hotels': 'Total Hotels (Size)',
                'Recent Updates': 'Recent Updates (Activity)',
                'Update Ratio': 'Update Frequency'
            },
            size_max=60,
            color_discrete_sequence=px.colors.qualitative.Vivid,
            trendline="lowess",
            trendline_color_override="#888"
        )
        
        # Add custom annotations and styling
        fig_activity.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Arial"
            ),
            xaxis=dict(
                gridcolor='#f0f0f0',
                type='log'  # Logarithmic scale for better distribution
            ),
            yaxis=dict(
                gridcolor='#f0f0f0'
            ),
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(240,240,240,0.5)'
        )
        
        # Add custom hover template
        fig_activity.update_traces(
            hovertemplate="<b>%{hover_name}</b><br>"
                          "Total Hotels: %{x}<br>"
                          "Recent Updates: %{y}<br>"
                          "Update Ratio: %{customdata:.2f}",
            customdata=df_activity['Update Ratio']
        )
        
        # Add explanatory annotation
        fig_activity.add_annotation(
            x=0.95,
            y=0.1,
            xref="paper",
            yref="paper",
            text="Higher right = Large & Active suppliers<br>"
                 "Upper left = Small but Active suppliers",
            showarrow=False,
            align="right",
            font=dict(color="#666")
        )
        
        st.plotly_chart(fig_activity, use_container_width=True)
        
        # Add metric boxes below
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Most Active Supplier", 
                     df_activity.loc[df_activity['Recent Updates'].idxmax()]['Supplier'],
                     help="Supplier with highest number of recent updates")
            
        with col2:
            st.metric("Largest Supplier", 
                     df_activity.loc[df_activity['Total Hotels'].idxmax()]['Supplier'],
                     help="Supplier with most total hotels")
            
        with col3:
            avg_ratio = df_activity['Update Ratio'].mean()
            st.metric("Average Update Ratio", 
                     f"{avg_ratio:.2f} updates/hotel",
                     help="Average updates per hotel across all suppliers")
        
    else:
        st.warning("Insufficient data for supplier activity analysis")
        
except Exception as e:
    st.error(f"Error generating activity analysis: {str(e)}")





import numpy as np





# Time-Series Trend Analysis
st.subheader("📈 Update Trends Over Time")
try:
    # Simulate time-series data (replace with actual data if available)
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    updates = np.random.poisson(lam=50, size=len(dates))  # Simulated daily updates
    new_data = np.random.poisson(lam=20, size=len(dates))  # Simulated new data additions
    
    df_trends = pd.DataFrame({
        "Date": dates,
        "Updates": updates,
        "New Data": new_data
    })
    
    # Create the time-series plot
    fig_trends = px.line(
        df_trends,
        x="Date",
        y=["Updates", "New Data"],
        title="Daily Update and New Data Trends",
        labels={"value": "Count", "variable": "Metric"},
        color_discrete_map={"Updates": "#1f77b4", "New Data": "#2ca02c"}
    )
    
    # Add range slider and annotations
    fig_trends.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        hovermode="x unified",
        plot_bgcolor="rgba(245,245,245,1)",
        paper_bgcolor="rgba(255,255,255,1)"
    )
    
    st.plotly_chart(fig_trends, use_container_width=True)
    
except Exception as e:
    st.warning(f"Could not generate time-series trends: {str(e)}")





# Detailed Supplier Breakdown
st.subheader("📊 Supplier Performance Breakdown")
try:
    if supplier_total and supplier_updates:
        # Create detailed supplier metrics
        df_supplier_details = pd.DataFrame([
            {
                "Supplier": supplier,
                "Total Hotels": int(total),
                "Recent Updates": int(supplier_updates.get(supplier, 0)),
                "Update Frequency": int(supplier_updates.get(supplier, 0)) / int(total) if int(total) > 0 else 0,
                "Success Rate": np.random.uniform(0.8, 0.95)  # Simulated success rate
            }
            for supplier, total in supplier_total.items()
        ])
        
        # Sort by total hotels
        df_supplier_details = df_supplier_details.sort_values("Total Hotels", ascending=False)
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Top Supplier by Hotels", df_supplier_details.iloc[0]["Supplier"])
        with col2:
            st.metric("Top Supplier by Updates", df_supplier_details.loc[df_supplier_details["Recent Updates"].idxmax()]["Supplier"])
        with col3:
            st.metric("Highest Success Rate", df_supplier_details.loc[df_supplier_details["Success Rate"].idxmax()]["Supplier"])
        
        # Display detailed table
        st.dataframe(
            df_supplier_details.style
                .background_gradient(cmap="Blues", subset=["Total Hotels"])
                .background_gradient(cmap="Greens", subset=["Recent Updates"])
                .background_gradient(cmap="Reds", subset=["Success Rate"]),
            use_container_width=True
        )
        
    else:
        st.warning("Insufficient data for detailed supplier breakdown")
        
except Exception as e:
    st.error(f"Error generating supplier breakdown: {str(e)}")










# Key Metrics Summary
st.subheader("📌 Key Metrics at a Glance")
try:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Suppliers", len(supplier_total))
    with col2:
        st.metric("Total Hotels", sum(int(v) for v in supplier_total.values()))
    with col3:
        st.metric("Total Updates", sum(int(v) for v in supplier_updates.values()))
    with col4:
        st.metric("Avg. Update Frequency", f"{df_supplier_details['Update Frequency'].mean():.2f}")
except Exception as e:
    st.warning(f"Could not display key metrics: {str(e)}")











# Sidebar Navigation
with st.sidebar:
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    /* Main sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 20px;
    }
    
    /* Navigation header */
    .sidebar-header h1 {
        color: white !important;
        font-family: 'Segoe UI', sans-serif;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 30px;
        text-align: center;
        letter-spacing: 0.5px;
    }
    
    /* Navigation items */
    .nav-item {
        padding: 12px 20px;
        margin: 8px 0;
        border-radius: 8px;
        transition: all 0.3s ease;
        font-size: 15px;
    }
    
    .nav-item:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
    }
    
    /* Separator styling */
    .separator {
        border-top: 1px solid rgba(255, 255, 255, 0.2);
        margin: 25px 0;
    }
    
    /* Filter section */
    .filter-section {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
    }
    
    /* About section */
    .about-section {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        margin-top: 20px;
    }
    
    /* Selectbox customization */
    .stSelectbox [data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar Header
    st.markdown('<div class="sidebar-header"><h1>📊 Data Navigator</h1></div>', unsafe_allow_html=True)

    # Navigation Menu with Icons
    st.markdown("""
    <div class="nav-menu">
        <div class="nav-item">📈 Global Overview</div>
        <div class="nav-item">🔍 Supplier Analysis</div>
        <div class="nav-item">📅 Trends Over Time</div>
        <div class="nav-item">🌍 Geospatial Map</div>
        <div class="nav-item">📋 Detailed Breakdown</div>
    </div>
    """, unsafe_allow_html=True)

    # Separator
    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # Filter Section
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown("**FILTERS**", help="Adjust these parameters to filter dataset")
    selected_supplier = st.selectbox("Select Supplier", list(supplier_total.keys()))
    st.markdown('</div>', unsafe_allow_html=True)

    # About Section
    st.markdown('<div class="about-section">', unsafe_allow_html=True)
    st.markdown("**ABOUT**")
    st.markdown("""
    <div style="font-size: 14px; line-height: 1.6; color: #e0e0e0;">
        This analytical dashboard provides insights into global hotel data mapping 
        and supplier performance metrics. Designed for data-driven decision making.
    </div>
    """, unsafe_allow_html=True)
    
    # Version & Copyright
    st.markdown("""
    <div style="margin-top: 20px; font-size: 12px; color: #a0a0a0;">
        Version: 2.1.0<br>
        © 2024 Hotel Data Analytics
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Company Logo (Add your logo URL)
    st.markdown("""
    <div style="text-align: center; margin-top: 30px;">
        <img src="https://via.placeholder.com/150x50.png?text=Company+Logo" 
             style="width: 150px; opacity: 0.8;">
    </div>
    """, unsafe_allow_html=True)