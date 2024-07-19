import pandas as pd
from datetime import datetime
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st
import io
import msoffcrypto
import numpy as np
import re
import time

pd.set_option('future.no_silent_downcasting', True)
pd.set_option('display.max_columns', None)
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stMultiSelect [data-baseweb=select] span{
            max-width: 250px;
            font-size: 0.7rem;
        }
    </style>
    """, unsafe_allow_html=True)

# Hide Streamlit style and buttons
hide_st_style = '''
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
'''
st.markdown(hide_st_style, unsafe_allow_html=True)

# Load file function
@st.cache_data
def loadfile():
    password = st.secrets["db_password"]
    excel_content = io.BytesIO()
    with open("T01_Main.xlsx", 'rb') as f:
        excel = msoffcrypto.OfficeFile(f)
        excel.load_key(password)
        excel.decrypt(excel_content)
    
    # Loading data from excel file
    df = pd.read_excel(excel_content, sheet_name="Sheet1")
    return df

# Main Program Starts Here
df = loadfile()

df["Description"] = [x.strip() for x in df["Description"]]

main_cat_order_list = [
    "Revenue Receipts",
    "Rev Recp - Tax Revenue Net",
    "Rev Recp - Non Tax Revenue",
    "Non Debt Capital Receipt",
    "Non Debt - Recovery of Loans",
    "Non Debt - Other Receipt",
    "Total Recp - RevRecp Plus NonDebtRecp",
    "Revenue Expenditure",
    "Rev Exp - Interest Payments",
    "Capital Expenditure",
    "Cap Exp - Loan Disbursed",
    "Total Exp - RevExp + CapExp",
    "Fiscal Deficit - TotalExp Minus TotalRecp",
    "Revenue Deficit - RevExp Minus RevRecp",
    "Primary Deficit - FisicalDef Minus InterestPay"
]

# Convert 'Date' column to datetime if not already done
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y').apply(lambda x : x.date())

# Convert 'Description' to a categorical type for sorting
df['Description'] = pd.Categorical(df['Description'], categories=main_cat_order_list, ordered=True)

# Sort the DataFrame by 'Date' (newest first) and 'Description'
df = df.sort_values(by=['Date', 'Description'], ascending=[True, False])

df["Actual % of BE"] = ((df["Actual"].astype(float)/df["BE"].astype(float))*100).round(2)

df["Actual"] = (df["Actual"].astype(float)/100000).round(2) #converting into Rs Lakk Cr
df["BE"] = (df["BE"].astype(float)/100000).round(2) #converting into Rs Lakk Cr

# Unique dates sorted
unique_dates = df['Date'].unique()
date_index = range(len(unique_dates))

# title_placeholder = st.empty()

# Sidebar for date index selection using a slider
selected_date_index = st.sidebar.slider("Select Date Index", 0, len(unique_dates) - 1, 0)

overall_actual_min_value = df['Actual'].min()
overall_actual_max_value = df['Actual'].max()

# Calculate the overall min and max values for the 'BE' column in the entire dataset
overall_be_min_value = df['BE'].min()
overall_be_max_value = df['BE'].max()

#Place the "Play" button at the top of the sidebar
play_button = st.sidebar.button("Play")
pause_button = st.sidebar.button("Pause")

slider_placeholder = st.sidebar.empty()

# Filter data based on selected date index
selected_date = unique_dates[selected_date_index]
filtered_data = df[df['Date'] == selected_date]

# Create subplot
fig = make_subplots(rows=1, cols=2, shared_yaxes=True, specs=[[{"type": "scatter"}, {"type": "bar"}]],column_widths=[0.75, 0.25], horizontal_spacing=0.01)

# Add scatter plot
fig.add_trace(go.Scatter(
    x=filtered_data['Actual'], y=filtered_data['Description'], mode='markers', name='Actual', marker=dict(size=15)
), row=1, col=1)


# Add horizontal bar chart
fig.add_trace(go.Bar(
    x=filtered_data['BE'], y=filtered_data['Description'], orientation='h', name='Budget Estimate',
), row=1, col=2)

# Adding Actual values as a line or bar on top of the BE bars
fig.add_trace(go.Bar(
    x=filtered_data['Actual'], y=filtered_data['Description'], orientation='h', name='Actual',
    marker=dict(color='red', opacity=0.6), # semi-transparent red bars for Actual
    textposition='outside', textfont=dict(size=15, family='Arial', color='black', weight='bold')
), row=1, col=2)

# Update layout
fig.update_layout(
    title='Financial Data Comparison by Date',
    xaxis_title='Actual Values',
    xaxis2_title='Budget Estimates',
    yaxis_title='Description',
    showlegend=False
)

# Update the y-axis tick labels to be bold
fig.update_yaxes(tickfont=dict(size=15, family='Arial', color='black', weight='bold'), row=1, col=1)

fig.update_layout(height=700, width=1200, margin=dict(l=5, r=10, t=0, b=0, pad=0), showlegend=False, yaxis=dict(automargin=True))

# Update the layout for the combined figure for 1
fig.update_xaxes(row=1, col=1, range=[0, overall_actual_max_value * 1.05], fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')
fig.update_yaxes(row=1, col=1, tickfont=dict(size=15),fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')

# Update the layout for the combined figure for 2
fig.update_xaxes(row=1, col=2, range=[0, overall_be_max_value * 1.05], fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')
fig.update_yaxes(row=1, col=2, tickfont=dict(size=15),fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')

# # Placeholder for the plot
plot_placeholder = st.empty()

# Display the plot in the placeholder
plot_placeholder.plotly_chart(fig, use_container_width=True)


# def update_title(selected_date):
#     # # Create the styled title
#     # styled_category_type = f"<span style='color:red; font-weight:bold;'>{selected_category_type}</span>"
#     # styled_sector_type = f"<span style='color:blue; font-weight:bold;'>{selected_sector_type}</span>"
#     # styled_metric_type = f"<span style='color:brown; font-weight:bold;'>{selected_metric_type}</span>"
#     styled_month = f"<span style='color:green; font-weight:bold;'>{selected_date.strftime('%b %Y')}</span>"
#     # title = f"Consumer Price {styled_category_type} {styled_sector_type} {styled_metric_type} Data For Month - {styled_month}"
#     title = f"Consumer Price Data For Month - {styled_month}"

#     # Display the date with month on top along with the title
#     title_placeholder.markdown(f"<h1 style='font-size:30px; margin-top: -20px;'>{title}</h1>", unsafe_allow_html=True)

# # Initialize title and slider
# if 'current_index' not in st.session_state:
#     st.session_state.current_index = 0

# if 'is_playing' not in st.session_state:
#     st.session_state.is_playing = False

# # Validate the current index
# if st.session_state.current_index >= len(unique_dates):
#     st.session_state.current_index = 0

# slider = slider_placeholder.slider("Slider for Selecting Date Index", min_value=0, max_value=len(unique_dates) - 1, value=st.session_state.current_index, key="date_slider")
# update_title(unique_dates[slider])

# if play_button:
#     st.session_state.is_playing = True
#     if st.session_state.current_index == len(unique_dates) - 1:
#         st.session_state.current_index = 0

# if pause_button:
#     st.session_state.is_playing = False

# if st.session_state.is_playing:
#     for i in range(st.session_state.current_index, len(unique_dates)):
#         if not st.session_state.is_playing:
#             break
#         selected_date = unique_dates[i]
#         update_plot(selected_date)
#         update_title(selected_date)
#         st.session_state.current_index = i
#         slider_placeholder.slider("Slider for Selecting Date Index", min_value=0, max_value=len(unique_dates) - 1, value=i, key=f"date_slider_{i}")
#         time.sleep(0.3)  # Adjust the sleep time to control the animation speed
# else:
#     selected_date = unique_dates[slider]
#     update_plot(selected_date)
#     update_title(selected_date)
#     st.session_state.current_index = slider
