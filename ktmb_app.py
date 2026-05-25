import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import altair as alt

# ----------------------------
# Forecast function
# ----------------------------
def data_by_service(df):
    df = df.copy()

    service = df.loc[0, 'service']
    ridership = df['ridership'].tolist()

    df['predict_ridership'] = df['ridership']

    # safe last 5 data
    last5_data = ridership[-5:] if len(ridership) >= 5 else ridership

    last_date = datetime.strptime(df['date'].iloc[-1], '%Y-%m-%d')

    count = 0

    while count <= 4:
        pdate = (last_date + timedelta(days=count+1)).strftime('%Y-%m-%d')

        avg_ridership = round(sum(last5_data[-5:]) / len(last5_data), 0)
        last5_data.append(avg_ridership)

        df.loc[len(df)] = {
            'date': pdate,
            'service': service,
            'ridership': float('nan'),
            'predict_ridership': avg_ridership
        }

        count += 1

    return df


def get_ktmb_data():
    URL_DATA = 'https://storage.data.gov.my/transportation/ktmb/ridership_ktmb_daily.parquet'
    df = pd.read_parquet(URL_DATA)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df


# ----------------------------
# Streamlit UI
# ----------------------------
st.title("KTMB Ridership Forecast")

df_ridership = get_ktmb_data()

# Dropdown service
service_list = df_ridership['service'].unique().tolist()
selected_service = st.selectbox("Select Service", service_list)

# Filter data
df_service = df_ridership[df_ridership['service'] == selected_service].copy()
df_service.reset_index(drop=True, inplace=True)

# Forecast
df_result = data_by_service(df_service)

# Convert types
df_result['date'] = pd.to_datetime(df_result['date'])
df_result['ridership'] = pd.to_numeric(df_result['ridership'], errors='coerce')
df_result['predict_ridership'] = pd.to_numeric(df_result['predict_ridership'], errors='coerce')

# Convert date (ensure datetime)
df_result['date'] = pd.to_datetime(df_result['date'])

# Get latest month
latest_date = df_result['date'].max()
latest_month = latest_date.month
latest_year = latest_date.year

# Filter latest month
df_latest_month = df_result[
    (df_result['date'].dt.month == latest_month) &
    (df_result['date'].dt.year == latest_year)
]

# Show table
st.subheader("Data Table")
st.dataframe(df_result, hide_index=True)

# Date range filter
min_date = df_result['date'].min()
max_date = df_result['date'].max()

date_range = st.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_result[
        (df_result['date'] >= pd.to_datetime(start_date)) &
        (df_result['date'] <= pd.to_datetime(end_date))
    ]
else:
    df_filtered = df_result

# Plot
st.subheader("Ridership Trend (Actual vs Predicted)")

# Base chart
base = alt.Chart(df_filtered)

# Bar chart for actual
bar = base.mark_bar(color='steelblue').encode(
    x=alt.X('date:T', title='Date'),
    y=alt.Y('ridership:Q', title='Ridership'),
    tooltip=['date:T', 'ridership:Q']
)

# Line chart for prediction
line = base.mark_line(color='orange', strokeDash=[5,5], point=True).encode(
    x='date:T',
    y='predict_ridership:Q',
    tooltip=['date:T', 'predict_ridership:Q']
).interactive()

# Combine both
chart = bar + line

st.altair_chart(chart, use_container_width=True)
