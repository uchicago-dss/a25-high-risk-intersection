import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

####################### Import Dataset #######################
data = pd.read_pickle('dataset.pkl')

####################### Plot 1 #######################
df = data.copy()

df['CRASH_DATE'] = pd.to_datetime(df['CRASH_DATE'])
df['CRASH_HOUR'] = df['CRASH_DATE'].dt.hour
df['CRASH_DAY_OF_WEEK'] = df['CRASH_DATE'].dt.day_name()

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

num_weeks = (df['CRASH_DATE'].max() - df['CRASH_DATE'].min()).days / 7

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
        marker=dict(size=5, color=colors[day], symbol='circle'),
        opacity=0.7
    ))

fig.update_layout(
    title='Hourly Crashes Across a Day',
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
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='lightgray'),
    plot_bgcolor='white',
    width=580,
    height=380
)

fig.write_html("plots/plot1.html")


####################### Plot 2 #######################
df = data.copy()
df['CRASH_DATE'] = pd.to_datetime(df['CRASH_DATE'])
df['hour'] = df['CRASH_DATE'].dt.hour
df['date'] = df['CRASH_DATE'].dt.date

def categorize(row):
    if row['Precipitation Type'] == 70:
        return 'Snow'
    elif row['Interval Rain'] > 0:
        return 'Rain'
    else:
        return 'Clear'

df['condition'] = df.apply(categorize, axis=1)

hourly_crashes = (
    df.groupby(['date','hour','condition'])['CRASH_RECORD_ID']
      .count()
      .reset_index()
      .rename(columns={'CRASH_RECORD_ID':'crash_count'})
)

hourly_avg = (
    hourly_crashes.groupby(['hour','condition'])['crash_count']
                  .mean()
                  .reset_index()
)

fig = px.bar(
    hourly_avg,
    x='hour',
    y='crash_count',
    color='condition',
    barmode='group',
    labels={'hour':'Hour of Day', 'crash_count':'Average Number of Crashes', 'condition':'Condition'},
    title='Average Hourly Crashes by Weather Condition',
    color_discrete_map={'Clear':'orange', 'Snow':'lightblue', 'Rain':'lightseagreen'}
)

fig.update_layout(
    xaxis=dict(tickmode='linear'),
    yaxis=dict(showgrid=True),
    plot_bgcolor='white',
    width=580,
    height=380
)

fig.write_html("plots/plot2.html")


####################### Plot 3 #######################
df = data.copy()
df = df[df['Precipitation Type'] != 70]
df['CRASH_DATE'] = pd.to_datetime(df['CRASH_DATE'])

df['year'] = df['CRASH_DATE'].dt.year
df['month'] = df['CRASH_DATE'].dt.month
df['day'] = df['CRASH_DATE'].dt.day
df['hour'] = df['CRASH_DATE'].dt.hour

exclude = []
mask = ~df[['year','month','day','hour']].apply(tuple, axis=1).isin(exclude)
df_filtered = df[mask]

hourly_per_day = df_filtered.groupby([
    df_filtered['CRASH_DATE'].dt.date.rename('date'),
    df_filtered['CRASH_DATE'].dt.hour.rename('hour')
]).agg({
    'CRASH_RECORD_ID': 'count',
    'Interval Rain': 'mean'
}).reset_index()

hourly_per_day.rename(columns={'CRASH_RECORD_ID': 'crash_count'}, inplace=True)

x = hourly_per_day['Interval Rain']
y = hourly_per_day['crash_count']
m, b = np.polyfit(x, y, 1)
y_fit = m*x + b

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x,
    y=y,
    mode='markers',
    marker=dict(color='lightseagreen', opacity=0.3),
    name='Hourly Crashes',
))

fig.add_trace(go.Scatter(
    x=x,
    y=y_fit,
    mode='lines',
    line=dict(color='black', width=2),
    name=f'Linear Regression: y={m:.2f}x+{b:.2f}',
))

fig.update_layout(
    legend=dict(
        orientation='h',
        y=-0.2,
        x=0.5,
        xanchor='center',
        yanchor='top'
    )
)


fig.update_layout(
    title='Hourly Traffic Crashes During Rain',
    xaxis_title='Hourly Rain (mm)',
    yaxis_title='Crash Count',
    plot_bgcolor='rgb(223, 223, 223)',
    paper_bgcolor='rgb(223, 223, 223)',
    xaxis=dict(showgrid=True, gridcolor='lightgray'),
    yaxis=dict(showgrid=True, gridcolor='lightgray'),
    width=580,
    height=380
)

fig.write_html("plots/plot3.html")

####################### Plot 4 #######################
df = df.copy()
df = df[df['Precipitation Type'] != 60]
df['CRASH_DATE'] = pd.to_datetime(df['CRASH_DATE'])

df['year'] = df['CRASH_DATE'].dt.year
df['month'] = df['CRASH_DATE'].dt.month
df['day'] = df['CRASH_DATE'].dt.day
df['hour'] = df['CRASH_DATE'].dt.hour

exclude = []
mask = ~df[['year','month','day','hour']].apply(tuple, axis=1).isin(exclude)
df_filtered = df[mask]

hourly_per_day = df_filtered.groupby([
    df_filtered['CRASH_DATE'].dt.date.rename('date'),
    df_filtered['CRASH_DATE'].dt.hour.rename('hour')
]).agg({
    'CRASH_RECORD_ID': 'count',
    'Interval Rain': 'mean'
}).reset_index()

hourly_per_day.rename(columns={'CRASH_RECORD_ID': 'crash_count'}, inplace=True)

x = hourly_per_day['Interval Rain']
y = hourly_per_day['crash_count']
m, b = np.polyfit(x, y, 1)
y_fit = m*x + b

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x,
    y=y,
    mode='markers',
    marker=dict(color='lightblue', opacity=0.5),
    name='Hourly Crashes'
))

fig.add_trace(go.Scatter(
    x=x,
    y=y_fit,
    mode='lines',
    line=dict(color='black', width=2),
    name=f'Linear Regression: y={m:.2f}x+{b:.2f}'
))

fig.update_layout(
    legend=dict(
        orientation='h',
        y=-0.2,
        x=0.5,
        xanchor='center',
        yanchor='top'
    )
)

fig.update_layout(
    title='Hourly Traffic Crashes During Snowfall',
    xaxis_title='Hourly Snow (mm)',
    yaxis_title='Crash Count',
    plot_bgcolor='rgb(223, 223, 223)',
    paper_bgcolor='rgb(223, 223, 223)',
    xaxis=dict(showgrid=True, gridcolor='lightgray'),
    yaxis=dict(showgrid=True, gridcolor='lightgray'),
    width=580,
    height=380
)

fig.write_html("plots/plot4.html")


####################### Plot 5 #######################
df = data.copy()
df = df[df['condition'].isin(['CLEAR', 'RAIN', 'SNOW'])]
df['CRASH_DATE'] = pd.to_datetime(df['CRASH_DATE'])

daily_crashes = df.groupby(
    df['CRASH_DATE'].dt.date.rename('date')
).agg({
    'CRASH_RECORD_ID': 'count',
    'condition': lambda x: x.mode()[0].capitalize()
}).reset_index()

daily_crashes.rename(columns={'CRASH_RECORD_ID': 'crash_count'}, inplace=True)

fig = px.violin(
    daily_crashes,
    x='condition',
    y='crash_count',
    color='condition',
    box=True,
    points='all',
    labels={'condition':'Condition', 'crash_count':'Daily Crash Count'},
    title='Daily Crash Count by Weather Condition',
    color_discrete_map={'Clear':'orange', 'Rain':'lightseagreen', 'Snow':'lightblue'}
)


fig.update_traces(marker=dict(opacity=0.5))

fig.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True),
    width=580,
    height=380
)

fig.write_html("plots/plot5.html")
