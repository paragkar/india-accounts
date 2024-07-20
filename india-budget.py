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
import colorsys

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
df["GDP_Current"] = (df["GDP_Current"].astype(float)/100000).round(2) #converting into Rs Lakk Cr
df["Actual % of GDP"] = ((df["Actual"].astype(float)/df["GDP_Current"].astype(float))*100).round(2)
df["BE % of GDP"] = ((df["BE"].astype(float)/df["GDP_Current"].astype(float))*100).round(2)

# Unique dates sorted
unique_dates = df['Date'].unique()
date_index = range(len(unique_dates))

title_placeholder = st.empty()
slider_placeholder = st.sidebar.empty()
plot_placeholder = st.empty()

overall_actual_min_value = df['Actual % of GDP'].min()
overall_actual_max_value = df['Actual % of GDP'].max()

# Calculate the overall min and max values for the 'BE' column in the entire dataset
overall_be_min_value = df['BE'].min()
overall_be_max_value = df['BE'].max()


# def get_color_map(descriptions):
#     # Get a list of colors from Plotly's built-in palettes
#     palette = px.colors.qualitative.Plotly  # This is an example, choose the palette that fits your aesthetic
#     # If there are more descriptions than colors in the palette, cycle through the palette
#     color_cycle = [palette[i % len(palette)] for i in range(len(descriptions))]
#     return dict(zip(descriptions, color_cycle))

def get_unique_colors(n):
    # Generate colors using HSV transformed to RGB
    hues = [x/n for x in range(n)]  # Generate n distinct hues
    colors = [colorsys.hsv_to_rgb(h, 1, 1) for h in hues]  # Convert HSV to RGB
    # Convert RGB from 0-1 to 0-255 scale and format as hex
    hex_colors = ['#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255)) for r, g, b in colors]
    return hex_colors

def get_color_map(descriptions):
    unique_descriptions = list(set(descriptions))
    num_descriptions = len(unique_descriptions)
    colors = get_unique_colors(num_descriptions)
    return dict(zip(unique_descriptions, colors))


def update_plot(selected_date):
    filtered_data = df[df['Date'] == selected_date]
    # fig = make_subplots(rows=1, cols=2, shared_yaxes=True, specs=[[{"type": "scatter"}, {"type": "bar"}]], column_widths=[0.75, 0.25], horizontal_spacing=0.01)
   
    color_map = get_color_map(filtered_data['Description'].unique())

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, specs=[[{"type": "bar"}, {"type": "bar"}]], column_widths=[0.7, 0.3], horizontal_spacing=0.01)


    # # Add scatter plot on the left with text labels
    # fig.add_trace(go.Scatter(
    #     x=filtered_data["Actual % of BE"], 
    #     y=filtered_data['Description'], 
    #     mode='markers+text',  # Include both markers and text
    #     name='Actual', 
    #     marker=dict(size=15),
    #     text=filtered_data["Actual % of BE"].round(2).astype(str), 
    #     textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
    #     textposition='middle right'  # Position text 
    # ), row=1, col=1)

    # Add bar charts on the left 1
    fig.add_trace(go.Bar(
        x=filtered_data['BE % of GDP'], 
        y=filtered_data['Description'], 
        orientation='h', 
        name='Budget Estimate % of GDP',
        marker=dict(
            color=[color_map[desc] for desc in filtered_data['Description']],
            line=dict(color='black', width=1)  # Thin black border
        ),  # Apply dynamic color map
        text=filtered_data['BE % of GDP'].round(2).astype(str), 
        textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
        textposition='outside'  # Position text 
    ), row=1, col=2)

    # Add bar charts on the left 2
    fig.add_trace(go.Bar(
        x=filtered_data['Actual % of GDP'], 
        y=filtered_data['Description'], 
        orientation='h', 
        name='Actual Spend % of GDP',
        marker=dict(color=[color_map[desc] for desc in filtered_data['Description']], opacity=0.5),  # Apply dynamic color map
        text=filtered_data['Actual % of GDP'].round(2).astype(str), 
        textfont=dict(size=15, family='Arial', color='black', weight='bold'),
        # marker=dict(color='red', opacity=0.6),
        textposition='outside'  # Position text 
    ), row=1, col=2)

    # Add bar charts on the right 1
    fig.add_trace(go.Bar(
        x=filtered_data['BE'], 
        y=filtered_data['Description'], 
        orientation='h', 
        name='Budget Estimate Rs Lakh Cr',
        marker=dict(
            color=[color_map[desc] for desc in filtered_data['Description']],
            line=dict(color='black', width=1)  # Thin black border
        ),
        text=filtered_data['BE'].round(2).astype(str), 
        textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
        textposition='outside'  # Position text 
    ), row=1, col=1)

     # Add bar charts on the right 2
    fig.add_trace(go.Bar(
        x=filtered_data['Actual'], 
        y=filtered_data['Description'], 
        orientation='h', 
        name='Actual Spend Rs Lakh Cr',
        marker=dict(color=[color_map[desc] for desc in filtered_data['Description']],opacity=0.5),  # Apply dynamic color map 
        text=filtered_data['Actual'].round(2).astype(str), 
        textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
        # marker=dict(color='red', opacity=0.6),
        textposition='outside'  # Position text 
    ), row=1, col=1)

    
    # Update the layout for the combined figure for 1
    fig.update_xaxes(row=1, col=2, range=[0, overall_actual_max_value * 1.15], fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')
    fig.update_yaxes(row=1, col=2, tickfont=dict(size=15),fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')

    # Update the layout for the combined figure for 2
    fig.update_xaxes(row=1, col=1, range=[0, overall_be_max_value * 1.2], fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')
    fig.update_yaxes(row=1, col=1, tickfont=dict(size=15),fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')

    # Update y-axes: remove y-axis labels from the first chart (left)
    # fig.update_yaxes(showticklabels=False, row=1, col=1)
    fig.update_yaxes(tickfont=dict(size=15, family='Arial', color='black', weight='bold'), row=1, col=1)

    # Update layout for axis properties to remove y-axis title and reclaim space
    fig.update_layout(
        title=f'Financial Data Comparison for {selected_date}',
        xaxis1_title='Absolute Values Rs Lakh Cr',
        xaxis2_title='Values % of GDP',
        xaxis1_title_font=dict(size=15, family='Arial', color='black', weight='bold'),
        xaxis2_title_font=dict(size=15, family='Arial', color='black', weight='bold'),
        showlegend=False,
        height=700, width=1200, margin=dict(l=5, r=10, t=0, b=0, pad=0),
        yaxis=dict(
            title='',  # No title
            showticklabels=True,  # Keep tick labels
            automargin=True  # Automatically adjust margin to tick labels
        )
    )

    # fig.update_layout(title=f'Financial Data Comparison for {selected_date}', xaxis_title='Actual Values', xaxis2_title='Budget Estimates', yaxis_title='', showlegend=False, height=700, width=1200, margin=dict(l=5, r=10, t=0, b=0, pad=0))
    plot_placeholder.plotly_chart(fig, use_container_width=True)


def update_title(selected_date):
    title = f"Financial Data Comparison for {selected_date.strftime('%B %d, %Y')}"
    title_placeholder.markdown(f"<h1 style='font-size:30px; margin-top: -20px;'>{title}</h1>", unsafe_allow_html=True)


# Initialize title and slider
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

# Validate the current index
if st.session_state.current_index >= len(unique_dates):
    st.session_state.current_index = 0

slider = slider_placeholder.slider("Slider for Selecting Date Index", min_value=0, max_value=len(unique_dates) - 1, value=st.session_state.current_index, key="date_slider")
selected_date = unique_dates[slider]
update_plot(selected_date)
update_title(selected_date)

# Synchronize the current_index with the slider
if slider != st.session_state.current_index:
    st.session_state.current_index = slider

# Place the "Play" and "Pause" button at the top of the sidebar with unique keys
play_button = st.sidebar.button("Play", key="play_button")
pause_button = st.sidebar.button("Pause", key="pause_button")

# Use these buttons in your control logic
if play_button:
    # Check if the current index is at the end, and reset if so
    if st.session_state.current_index >= len(unique_dates) - 1:
        st.session_state.current_index = 0
    st.session_state.is_playing = True

if pause_button:
    st.session_state.is_playing = False
    update_plot(unique_dates[st.session_state.current_index])
    update_title(unique_dates[st.session_state.current_index])

# Slider updates should trigger the plot and title updates outside the loop
# selected_date = unique_dates[slider]
update_plot(selected_date)
update_title(selected_date)

# Animation loop controlled by the play button
if st.session_state.get('is_playing', False):
    start_index = st.session_state.current_index
    for i in range(start_index, len(unique_dates)):
        if not st.session_state.is_playing:
            break
        selected_date = unique_dates[i]
        update_plot(selected_date)
        update_title(selected_date)
        st.session_state.current_index = i
        slider_placeholder.slider("Slider for Selecting Date Index", min_value=0, max_value=len(unique_dates) - 1, value=i, key=f"date_slider_{i}")
        time.sleep(0.5)  # Adjust sleep time to control

