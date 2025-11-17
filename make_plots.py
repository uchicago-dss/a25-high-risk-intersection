import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv('filtered_crash_dataset.csv')

colors = {
    'Sunday': 'black',
    'Monday': 'lightcoral',
    'Tuesday': 'orange',
    'Wednesday': 'lawngreen',
    'Thursday': 'red',
    'Friday': 'blue',
    'Saturday': 'darkviolet'
}
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

df['CRASH_DATE'] = pd.to_datetime(df['CRASH_DATE'])

num_weeks = (df['CRASH_DATE'].iloc[0] - df['CRASH_DATE'].iloc[-1]).days / 7

hourly = (
    df.groupby(['CRASH_DAY_OF_WEEK', 'CRASH_HOUR'])
    .size()
    .reset_index(name='Count')
)

hourly['CRASH_DAY_OF_WEEK'] = pd.Categorical(hourly['CRASH_DAY_OF_WEEK'], categories=days)
hourly = hourly.sort_values(['CRASH_DAY_OF_WEEK', 'CRASH_HOUR'])

fig = go.Figure()

for day in days:
    day_data = hourly[hourly['CRASH_DAY_OF_WEEK'] == day]
    fig.add_trace(go.Scatter(
        x=day_data['CRASH_HOUR'],
        y=day_data['Count'] / num_weeks,
        mode='lines+markers',
        name=day,
        line=dict(width=2, color=colors[day]),
        marker=dict(
            size=5,
            color=colors[day],
            symbol='circle',
        ),
        opacity=0.7
    ))

fig.update_layout(
    title='Average Number of Crashes per Hour',
    xaxis_title='Hour',
    yaxis_title='Number of Crashes',
    legend_title='Day of Week',
    xaxis=dict(
        tickmode='linear',
        tick0=0,
        dtick=1,
        range=[0, 23],
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    ),
    yaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    ),
    plot_bgcolor='white',
    width=600,
    height=400
)

fig.write_html("crashes_chart.html")