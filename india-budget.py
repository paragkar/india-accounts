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
    /* Adjust the position of the markdown text container */
    .reportview-container .markdown-text-container {
        position: relative;
        top: -20px;  /* Adjust this value to move the title up */
    }
    /* Adjust header styling to remove space and lines */
    h1 {
        margin-top: -50px !important;  /* Decrease the space above the title */
        border-bottom: none !important;  /* Ensures no line is under the title */
    }
    /* Hide any horizontal rules that might be appearing */
    hr {
        display: none !important;
    }
    /* Reduce padding on the left and right sides of the main block container */
    .reportview-container .main .block-container{
        padding-left: -20px;
        padding-right: 10px;
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


#List for defining sorting order for "Main Category" & "Tax Details"
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

tax_order_list = [
    "Gross Tax Revenue",
    "Corporation Tax",
    "Income Tax",
    "Goods & Service Tax",
    "UT GST",
    "Customs",
    "Union Excise Duties",
    "Service Tax",
    "Other Taxes",
    "NCCD to NDRF",
    "Assignment to States",
    "GST Comp Cess",
    "IGST"
]

# Load file function
@st.cache_data
def loadfilemain():
    password = st.secrets["db_password"]
    excel_content = io.BytesIO()
    with open("T01_Main.xlsx", 'rb') as f:
        excel = msoffcrypto.OfficeFile(f)
        excel.load_key(password)
        excel.decrypt(excel_content)
    
    # Loading data from excel file
    df = pd.read_excel(excel_content, sheet_name="Sheet1")
    return df

# Load file function
@st.cache_data
def loadfiletax():
    password = st.secrets["db_password"]
    excel_content = io.BytesIO()
    with open("T02_TAX_Details.xlsx", 'rb') as f:
        excel = msoffcrypto.OfficeFile(f)
        excel.load_key(password)
        excel.decrypt(excel_content)
    
    # Loading data from excel file
    df = pd.read_excel(excel_content, sheet_name="Sheet1")
    return df

 #Load file function
@st.cache_data
def loadfileexp():
    password = st.secrets["db_password"]
    excel_content = io.BytesIO()
    with open("T12_Expenditure.xlsx", 'rb') as f:
        excel = msoffcrypto.OfficeFile(f)
        excel.load_key(password)
        excel.decrypt(excel_content)
    
    # Loading data from excel file
    df = pd.read_excel(excel_content, sheet_name="Sheet1")
    return df

# Main Program Starts Here

# Initialize title and slider
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False

if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None

# Sidebar for category selection
with st.sidebar:
    selected_category = st.selectbox("Select Category", ["Main Category", "Tax Details", "Expenditure Details"], key='category_select')
    # Check if category has changed
    if st.session_state.selected_category != selected_category:
        st.session_state.selected_category = selected_category
        st.session_state.is_playing = False  # Auto-pause if category changes

def loaddata():
    if selected_category == "Main Category":
        df = loadfilemain()
        cat_order_list = main_cat_order_list
    if selected_category == "Tax Details":
        df = loadfiletax()
        cat_order_list = tax_order_list
    return df, cat_order_list

def sort_and_filter_dataframe(df, category, top_n):
    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y')

    if category !='All':
        # Filter based on the category selected by the user
        df = df[df['Description'].str.contains(category)]

    # Identify the latest date
    latest_date = df['Date'].max()

    # Get the ordering for the latest date based on 'BE' values for the selected category
    top_descriptions = df[df['Date'] == latest_date].sort_values(by='BE', ascending=False)['Description'].head(top_n).tolist()

    # Filter the DataFrame to keep only rows with descriptions in the top 20 list
    df = df[df['Description'].isin(top_descriptions)]

    # Define categorical type with top descriptions only
    all_descriptions = pd.CategoricalDtype(categories=top_descriptions, ordered=True)
    df['Description'] = df['Description'].astype(all_descriptions)

    # Sort DataFrame by 'Date' and ordered 'Description'
    df_sorted = df.sort_values(by=['Date', 'Description'],ascending=[True, False])

    return df_sorted



#Loading Data
if selected_category in ["Main Category", "Tax Details"]:
    df, cat_order_list = loaddata()
    df["Description"] = [x.strip() for x in df["Description"]]
    # Convert 'Date' column to datetime if not already done
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%y').apply(lambda x : x.date())
    # Convert 'Description' to a categorical type for sorting
    df['Description'] = pd.Categorical(df['Description'], categories=cat_order_list, ordered=True)
    # Sort the DataFrame by 'Date' (newest first) and 'Description'
    df = df.sort_values(by=['Date', 'Description'], ascending=[True, False])

#Loading Data
if selected_category in ["Expenditure Details"]:
    df = loadfileexp()
    # Dropdown for user to choose between 'Revenue' and 'Capital'
    category_choice = st.sidebar.selectbox('Select Category:', ['All','Revenue', 'Capital'])
    # Numeric input for user to specify how many top items to display
    top_n = st.sidebar.number_input('Number of Top Items:', min_value=1, max_value=100, value=20)
    df = sort_and_filter_dataframe(df, category_choice, top_n)

#Processing Loaded Data
if selected_category in ["Main Category", "Expenditure Details"]:
    df["Actual % of BE"] = ((df["Actual"].astype(float)/df["BE"].astype(float))*100).round(2)
    df["Actual"] = (df["Actual"].astype(float)/100000).round(2) #converting into Rs Lakh Cr
    df["BE"] = (df["BE"].astype(float)/100000).round(2) #converting into Rs Lakh Cr
    df["GDP_Current"] = (df["GDP_Current"].astype(float)/100000).round(2) #converting into Rs Lakh Cr
    df["Actual % of GDP"] = ((df["Actual"].astype(float)/df["GDP_Current"].astype(float))*100).round(2)
    df["BE % of GDP"] = ((df["BE"].astype(float)/df["GDP_Current"].astype(float))*100).round(2)
    fig2_xaxis_min_value = df['Actual % of GDP'].min()
    fig2_xaxis_max_value = df['Actual % of GDP'].max()
    fig1_xaxis_min_value = df['BE'].min()
    fig1_xaxis_max_value = df['BE'].max()
    xaxis1_title = 'Absolute Values Rs Lakh Cr (Top Bar - Actuals, Bottom Bar - BE)'
    xaxis2_title ='Values % of GDP'

if selected_category == "Tax Details":
    df["Tax Cum Value"] = (df["Month_Cum_Year_CY"].astype(float)/100000).round(2) #converting into Rs Lakh Cr
    df["Tax Cum Value % of GDP"] = ((df["Month_Cum_Year_CY"].astype(float)/df["GDP_Current"].astype(float))*100).round(2)
    fig2_xaxis_min_value = df['Tax Cum Value % of GDP'].min()
    fig2_xaxis_max_value = df['Tax Cum Value % of GDP'].max()
    fig1_xaxis_min_value = df["Tax Cum Value"].min()
    fig1_xaxis_max_value = df["Tax Cum Value"].max()
    xaxis1_title = 'Tax Cum Value Rs Lakh Cr'
    xaxis2_title = 'Tax Cum Value % of GDP'

# Unique dates sorted
unique_dates = df['Date'].unique()
date_index = range(len(unique_dates))

title_placeholder = st.empty()
slider_placeholder = st.sidebar.empty()
plot_placeholder = st.empty()


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

def get_financial_year(date):
    year = date.year
    if date.month < 4:
        year -= 1
    return f'FY{year % 100:02d}-{(year + 1) % 100:02d}'

# def update_title(selected_date, selected_category):
#     # Convert the selected_date to a datetime object if it isn't one already
#     if isinstance(selected_date, str):
#         selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
#     # Get the financial year string
#     fy = get_financial_year(selected_date)
    
#     # Format the date correctly with ordinal suffix
#     day_suffix = lambda n: 'th' if 11 <= n <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
#     formatted_date = selected_date.strftime(f'%b {selected_date.day}{day_suffix(selected_date.day)}, %Y')

#     if selected_category == "Main Category":
#         # Prepare the title with financial year and formatted date
#         title = f"Central Government's Accounts For <span style='color:blue;'>{fy}</span> - <span style='color:red;'>{formatted_date}</span>"
#     if selected_category == "Expenditure Details":
#         # Prepare the title with financial year and formatted date
#         title = f"Central Government's Expenditure For <span style='color:blue;'>{fy}</span> - <span style='color:red;'>{formatted_date}</span>"
#     if selected_category == "Tax Details":
#          # Prepare the title with financial year and formatted date
#         title = f"Central Government's Tax Collection Details <span style='color:blue;'>{fy}</span> - <span style='color:red;'>{formatted_date}</span>"


#     # Use additional CSS to ensure the title is positioned correctly
#     title_css = """
#     <style>
#         h1 {
#             text-align: center; /* Center align the title */
#             margin-top: -20px !important; /* Adjust top margin to reduce gap */
#             margin-bottom: 5px; /* Add a bit of margin below the title if needed */
#             border-bottom: none !important; /* Ensures no line is under the title */
#         }
#     </style>
#     """

#     # Display the title with custom styling
#     st.markdown(title_css, unsafe_allow_html=True)
#     title_placeholder.markdown(f"<h1 style='font-size:30px;'>{title}</h1>", unsafe_allow_html=True) #End of Function Update title


def update_title(selected_date, selected_category):
    # Convert the selected_date to a datetime object if it isn't one already
    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    # Get the financial year string
    fy = get_financial_year(selected_date)
    
    # Format the date correctly with ordinal suffix
    day_suffix = lambda n: 'th' if 11 <= n <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    formatted_date = selected_date.strftime(f'%b {selected_date.day}{day_suffix(selected_date.day)}, %Y')

    if selected_category == "Expenditure Details":
        # Prepare the title with financial year, formatted date, and total values
        total_be = df[df['Date'] == selected_date]['BE'].sum().round(2)
        total_actual = df[df['Date'] == selected_date]['Actual'].sum().round(2)
        title = f"Central Government's Expenditure For <span style='color:blue;'>{fy}</span> - <span style='color:red;'>{formatted_date}</span> - Total BE: Rs {total_be} Lakh Cr, Total Actual: Rs {total_actual} Lakh Cr"
    else:
        # Prepare the title with financial year and formatted date for other categories
        if selected_category == "Main Category":
            title = f"Central Government's Accounts For <span style='color:blue;'>{fy}</span> - <span style='color:red;'>{formatted_date}</span>"
        elif selected_category == "Tax Details":
            title = f"Central Government's Tax Collection Details <span style='color:blue;'>{fy}</span> - <span style='color:red;'>{formatted_date}</span>"

    # Use additional CSS to ensure the title is positioned correctly and reduced in size
    title_css = """
    <style>
        h1 {
            text-align: center; /* Center align the title */
            margin-top: -20px !important; /* Adjust top margin to reduce gap */
            margin-bottom: 5px; /* Add a bit of margin below the title if needed */
            border-bottom: none !important; /* Ensures no line is under the title */
            font-size: 30px; /* Adjust font size to 80% of the original */
        }
    </style>
    """

    # Display the title with custom styling
    st.markdown(title_css, unsafe_allow_html=True)
    title_placeholder.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)


def update_plot(selected_date, selected_category):
    filtered_data = df[df['Date'] == selected_date]
    
    color_map = get_color_map(filtered_data['Description'].unique())

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, specs=[[{"type": "bar"}, {"type": "bar"}]], column_widths=[0.7, 0.3], horizontal_spacing=0.01)

    if selected_category in ["Main Category", "Expenditure Details"]:

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
            marker=dict(
                color=[color_map[desc] for desc in filtered_data['Description']],opacity=0.5,
                line=dict(color='black', width=1)  # Thin black border
            ),
            text=filtered_data['Actual'].round(2).astype(str), 
            textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
            # marker=dict(color='red', opacity=0.6),
            textposition='outside'  # Position text 
        ), row=1, col=1)

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
            text=filtered_data['BE % of GDP'].round(2).astype(str)+"%", 
            textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
            textposition='outside'  # Position text 
        ), row=1, col=2)

        # Add bar charts on the left 2
        fig.add_trace(go.Bar(
            x=filtered_data['Actual % of GDP'], 
            y=filtered_data['Description'], 
            orientation='h', 
            name='Actual Spend % of GDP',
            marker=dict(
                color=[color_map[desc] for desc in filtered_data['Description']],opacity=0.5,
                line=dict(color='black', width=1)  # Thin black border
            ),
            text=filtered_data['Actual % of GDP'].round(2).astype(str) + "%", 
            textfont=dict(size=15, family='Arial', color='black', weight='bold'),
            # marker=dict(color='red', opacity=0.6),
            textposition='outside'  # Position text 
        ), row=1, col=2)


    if selected_category == "Tax Details":

        # Add bar charts on the right 1
        fig.add_trace(go.Bar(
            x=filtered_data['Tax Cum Value'], 
            y=filtered_data['Description'], 
            orientation='h', 
            name='Tax Cumulative Value Rs Lakh Cr',
            marker=dict(
                color=[color_map[desc] for desc in filtered_data['Description']],
                line=dict(color='black', width=1)  # Thin black border
            ),
            text=filtered_data['Tax Cum Value'].round(2).astype(str), 
            textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
            textposition='outside'  # Position text 
        ), row=1, col=1)

        # Add bar charts on the left 1
        fig.add_trace(go.Bar(
            x=filtered_data['Tax Cum Value % of GDP'], 
            y=filtered_data['Description'], 
            orientation='h', 
            name='Tax Cum Value % of GDP',
            marker=dict(
                color=[color_map[desc] for desc in filtered_data['Description']],
                line=dict(color='black', width=1)  # Thin black border
            ),  # Apply dynamic color map
            text=filtered_data['Tax Cum Value % of GDP'].round(2).astype(str)+"%", 
            textfont=dict(size=15, family='Arial', color='black', weight='bold'), 
            textposition='outside'  # Position text 
        ), row=1, col=2)

    
    # Update the layout for the combined figure for 1
    fig.update_xaxes(row=1, col=2, range=[0, fig2_xaxis_max_value * 1.15], fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')
    fig.update_yaxes(row=1, col=2, tickfont=dict(size=15),fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')

    # Update the layout for the combined figure for 2
    fig.update_xaxes(row=1, col=1, range=[0, fig1_xaxis_max_value * 1.2], fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')
    fig.update_yaxes(row=1, col=1, tickfont=dict(size=15),fixedrange=True, showline=True, linewidth=1.5, linecolor='grey', mirror=True, showgrid=True, gridcolor='lightgrey')

    # Update y-axes: remove y-axis labels from the first chart (left)
    fig.update_yaxes(tickfont=dict(size=15, family='Arial', color='black', weight='bold'), row=1, col=1)

    # Update layout for axis properties to remove y-axis title and reclaim space
    fig.update_layout(
        # title=f'Financial Data Comparison for {selected_date}',
        # title_font=dict(size=15, family='Arial', color='black', weight='bold'),
        plot_bgcolor="white",  # Ensures background doesn't add unexpected styles
        paper_bgcolor="white",
        xaxis1_title= xaxis1_title,
        xaxis2_title= xaxis2_title,
        xaxis1_title_font=dict(size=15, family='Arial', color='black', weight='bold'),
        xaxis2_title_font=dict(size=15, family='Arial', color='black', weight='bold'),
        showlegend=False,
        height=700, width=1200, margin=dict(l=0, r=10, t=0, b=0, pad=0),
        yaxis=dict(
            title='',  # No title
            showticklabels=True,  # Keep tick labels
            automargin=True  # Automatically adjust margin to tick labels
        ),
    )


    update_title(selected_date, selected_category)

    plot_placeholder.plotly_chart(fig, use_container_width=True) #End of function update plot



#Animation of plot part of the code
# Setup columns for buttons
col1, col2 = st.columns(2)
with col1:
    prev_button = st.button('Previous')
with col2:
    next_button = st.button('Next')

# Handle previous and next button functionality
if prev_button:
    if st.session_state.current_index > 0:
        st.session_state.is_playing = False
        st.session_state.current_index -= 1
elif next_button:
    if st.session_state.current_index < len(unique_dates) - 1:
        st.session_state.current_index += 1

slider = slider_placeholder.slider("Slider for Selecting Date Index", min_value=0, max_value=len(unique_dates) - 1, value=st.session_state.current_index, key="date_slider")
selected_date = unique_dates[slider]
update_plot(selected_date, selected_category)
update_title(selected_date, selected_category)

# Synchronize the current_index with the slider
if slider != st.session_state.current_index:
    st.session_state.current_index = slider
    # Explicitly trigger updates
    selected_date = unique_dates[slider]
    update_plot(selected_date, selected_category)
    update_title(selected_date, selected_category)
    st.experimental_rerun()  # Optionally force a rerun if necessary

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
    update_plot(unique_dates[st.session_state.current_index],selected_category)
    update_title(unique_dates[st.session_state.current_index],selected_category)

# Slider updates should trigger the plot and title updates outside the loop
# selected_date = unique_dates[slider]
update_plot(selected_date, selected_category)
update_title(selected_date, selected_category)

# Animation loop controlled by the play button
if st.session_state.get('is_playing', False):
    start_index = st.session_state.current_index
    for i in range(start_index, len(unique_dates)):
        if not st.session_state.is_playing:
            break
        selected_date = unique_dates[i]
        update_plot(selected_date, selected_category)
        update_title(selected_date, selected_category)
        st.session_state.current_index = i
        slider_placeholder.slider("Slider for Selecting Date Index", min_value=0, max_value=len(unique_dates) - 1, value=i, key=f"date_slider_{i}")
        time.sleep(0.5)  # Adjust sleep time to control


