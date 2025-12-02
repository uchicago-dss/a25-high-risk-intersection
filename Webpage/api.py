from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pandas as pd
import os
from typing import Optional
import folium
from folium.plugins import HeatMap

app = FastAPI()

# Enable CORS so Vue frontend can access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to your dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "Newnew_dataset.csv")

# Load data once at startup
df_cache = None

# Cause categories from st_ranking2.py
USER_ERROR = ['DRIVING SKILLS/KNOWLEDGE/EXPERIENCE', 'FAILING TO REDUCE SPEED TO AVOID CRASH', 
    'IMPROPER OVERTAKING/PASSING', 'FOLLOWING TOO CLOSELY', 'DISTRACTION - FROM OUTSIDE VEHICLE',
    'FAILING TO YIELD RIGHT-OF-WAY', 'DISREGARDING STOP SIGN', 'IMPROPER LANE USAGE',
    'IMPROPER TURNING/NO SIGNAL', 'OPERATING VEHICLE IN ERRATIC, RECKLESS, CARELESS, NEGLIGENT OR AGGRESSIVE MANNER',
    'IMPROPER BACKING', 'DISTRACTION - FROM INSIDE VEHICLE', 'DRIVING ON WRONG SIDE/WRONG WAY',
    'DISREGARDING TRAFFIC SIGNALS', 'CELL PHONE USE OTHER THAN TEXTING', 'PHYSICAL CONDITION OF DRIVER',
    'DISREGARDING OTHER TRAFFIC SIGNS', 'RELATED TO BUS STOP', 'DISREGARDING ROAD MARKINGS',
    'TURNING RIGHT ON RED', 'UNDER THE INFLUENCE OF ALCOHOL/DRUGS (USE WHEN ARREST IS EFFECTED)',
    'HAD BEEN DRINKING (USE WHEN ARREST IS NOT MADE)', 'TEXTING', 'OBSTRUCTED CROSSWALKS',
    'DISTRACTION - OTHER ELECTRONIC DEVICE (NAVIGATION DEVICE, DVD PLAYER, ETC.)',
    'PASSING STOPPED SCHOOL BUS', 'DISREGARDING YIELD SIGN', 'BICYCLE ADVANCING LEGALLY ON RED LIGHT',
    'MOTORCYCLE ADVANCING LEGALLY ON RED LIGHT', 'EXCEEDING AUTHORIZED SPEED LIMIT',
    'EXCEEDING SAFE SPEED FOR CONDITIONS']

NON_USER_ERROR = ['ANIMAL', 'ROAD ENGINEERING/SURFACE/MARKING DEFECTS',
    'VISION OBSCURED (SIGNS, TREE LIMBS, BUILDINGS, ETC.)',
    'EVASIVE ACTION DUE TO ANIMAL, OBJECT, NONMOTORIST', 'WEATHER', 'ROAD CONSTRUCTION/MAINTENANCE']

VEHICLE_ERROR = ['EQUIPMENT - VEHICLE CONDITION']


def get_dataframe():
    global df_cache
    if df_cache is None:
        df_cache = pd.read_csv(DATA_PATH)
        df_cache["COUNT"] = 1
        # Convert date column
        if "CRASH_DATE_ONLY" in df_cache.columns:
            df_cache["CRASH_DATE_ONLY"] = pd.to_datetime(df_cache["CRASH_DATE_ONLY"])
    return df_cache.copy()


def apply_filters(df, date_start, date_end, damage, crash_type, injuries, cause, lighting):
    """Apply all filters to dataframe"""
    # Apply date filter
    if date_start:
        start_dt = pd.to_datetime(date_start)
        df = df[df["CRASH_DATE_ONLY"] >= start_dt]
    if date_end:
        end_dt = pd.to_datetime(date_end)
        df = df[df["CRASH_DATE_ONLY"] <= end_dt]
    
    # Apply damage filter
    if damage:
        damage_list = damage.split(',')
        df = df[df["DAMAGE"].isin(damage_list)]
    
    # Apply crash type filter
    if crash_type:
        crash_list = crash_type.split(',')
        df = df[df["CRASH_TYPE"].isin(crash_list)]
    
    # Apply injury filter
    if injuries:
        injury_list = injuries.split(',')
        injury_conditions = []
        if 'none' in injury_list:
            injury_conditions.append(df["INJURY_SCORE"] == 0)
        if 'non_incapacitating' in injury_list:
            injury_conditions.append(df["INJURIES_NON_INCAPACITATING"] > 0)
        if 'incapacitating' in injury_list:
            injury_conditions.append(df["INJURIES_INCAPACITATING"] > 0)
        if 'fatal' in injury_list:
            injury_conditions.append(df["INJURIES_FATAL"] > 0)
        
        if injury_conditions:
            combined = injury_conditions[0]
            for cond in injury_conditions[1:]:
                combined = combined | cond
            df = df[combined]
    
    # Apply cause filter
    if cause:
        cause_list = cause.split(',')
        cause_values = []
        if 'user' in cause_list:
            cause_values.extend(USER_ERROR)
        if 'non_user' in cause_list:
            cause_values.extend(NON_USER_ERROR)
        if 'vehicle' in cause_list:
            cause_values.extend(VEHICLE_ERROR)
        
        if cause_values:
            cause_col = None
            for col in ['PRIM_CONTRIBUTORY_CAUSE', 'PRIMARY_CONTRIBUTORY_CAUSE', 'PRIMARY_CAUSE']:
                if col in df.columns:
                    cause_col = col
                    break
            if cause_col:
                df = df[df[cause_col].isin(cause_values)]
    
    # Apply lighting filter
    if lighting:
        lighting_list = lighting.split(',')
        df = df[df["LIGHTING_CONDITION"].isin(lighting_list)]
    
    return df


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "API is running"}


@app.get("/api/map", response_class=HTMLResponse)
def get_map(
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    damage: Optional[str] = Query(None),
    crash_type: Optional[str] = Query(None),
    injuries: Optional[str] = Query(None),
    cause: Optional[str] = Query(None),
    lighting: Optional[str] = Query(None)
):
    """Generate Folium heatmap with filters applied"""
    try:
        df = get_dataframe()
        df = apply_filters(df, date_start, date_end, damage, crash_type, injuries, cause, lighting)
        
        # Prepare data for map
        map_df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
        map_df = map_df[(map_df['LATITUDE'] != 0) & (map_df['LONGITUDE'] != 0)]
        
        if map_df.empty:
            # Return empty map centered on Chicago
            m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles='CartoDB dark_matter')
            return m._repr_html_()
        
        # Sample if too large for performance
        if len(map_df) > 10000:
            map_df = map_df.sample(n=10000, random_state=42)
        
        # Create map centered on the data
        center_lat = map_df['LATITUDE'].mean()
        center_lon = map_df['LONGITUDE'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='CartoDB dark_matter'
        )
        
        # Prepare heatmap data
        heat_data = []
        for _, row in map_df.iterrows():
            if not pd.isna(row['LATITUDE']) and not pd.isna(row['LONGITUDE']):
                heat_data.append([row['LATITUDE'], row['LONGITUDE']])
        
        if heat_data:
            HeatMap(
                heat_data,
                radius=15,
                blur=12,
                max_zoom=13,
                min_opacity=0.3,
                gradient={
                    0.0: 'rgba(0, 0, 255, 0)',
                    0.2: 'rgba(0, 255, 255, 0.5)',
                    0.4: 'rgba(0, 255, 0, 0.6)',
                    0.6: 'rgba(255, 255, 0, 0.7)',
                    0.8: 'rgba(255, 128, 0, 0.8)',
                    1.0: 'rgba(255, 0, 0, 0.9)'
                }
            ).add_to(m)
        
        return m._repr_html_()
    except Exception as e:
        return f"<html><body><h2>Error loading map: {str(e)}</h2></body></html>"


@app.get("/api/ranking")
def get_ranking(
    rank_type: str = Query("frequency"),
    group_by: str = Query("street"),
    limit: int = Query(10),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    damage: Optional[str] = Query(None),
    crash_type: Optional[str] = Query(None),
    injuries: Optional[str] = Query(None),
    cause: Optional[str] = Query(None),
    lighting: Optional[str] = Query(None)
):
    """Get crash location rankings with filters"""
    try:
        df = get_dataframe()
        df = apply_filters(df, date_start, date_end, damage, crash_type, injuries, cause, lighting)
        
        # Check if data is empty
        if df.empty:
            return {
                "ranking": [],
                "rank_type": rank_type,
                "group_by": group_by,
                "total_crashes": 0,
                "message": "No data matches your filter criteria"
            }
        
        delta = 0.00045
        
        # Create location bins
        df['LAT_BIN'] = (df['LATITUDE'] / delta).round().astype(int)
        df['LON_BIN'] = (df['LONGITUDE'] / delta).round().astype(int)
        df['LOCATION_BIN'] = df['LAT_BIN'].astype(str) + "_" + df['LON_BIN'].astype(str)
        
        # Group data
        if group_by == "street":
            ranking = df.groupby('STREET_NAME').sum(numeric_only=True)
            ranking['name'] = ranking.index
        else:  # location
            ranking = df.groupby('LOCATION_BIN').sum(numeric_only=True)
            ranking["LAT_BIN"] = ranking.index.map(lambda x: int(x.split("_")[0]))
            ranking["LON_BIN"] = ranking.index.map(lambda x: int(x.split("_")[1]))
            ranking["LATITUDE"] = round(ranking["LAT_BIN"] * delta, 5)
            ranking["LONGITUDE"] = round(ranking["LON_BIN"] * delta, 5)
            ranking["name"] = ranking["LATITUDE"].astype(str) + ", " + ranking["LONGITUDE"].astype(str)
        
        # Calculate months for crashes per month
        if date_start and date_end:
            start_dt = pd.to_datetime(date_start)
            end_dt = pd.to_datetime(date_end)
        else:
            start_dt = pd.to_datetime('2017-10-24')
            end_dt = pd.to_datetime('2025-10-24')
        
        months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
        ranking["CRASHES_PER_MONTH"] = (ranking["COUNT"] / months).round(2)
        
        # Apply ranking type
        if rank_type == "frequency":
            ranking = ranking.sort_values(by='COUNT', ascending=False)
            result_cols = ['name', 'COUNT', 'CRASHES_PER_MONTH']
        elif rank_type == "weighted":
            ranking = ranking.sort_values(by='INJURY_SCORE', ascending=False)
            result_cols = ['name', 'INJURIES_FATAL', 'INJURIES_INCAPACITATING', 
                          'INJURIES_NON_INCAPACITATING', 'COUNT', 'CRASHES_PER_MONTH', 'INJURY_SCORE']
        else:  # dangerous
            ranking["AVERAGE_INJURY_SCORE"] = ranking["INJURY_SCORE"] / ranking["COUNT"]
            ranking = ranking.sort_values(by='AVERAGE_INJURY_SCORE', ascending=False)
            result_cols = ['name', 'INJURIES_FATAL', 'INJURIES_INCAPACITATING',
                          'INJURIES_NON_INCAPACITATING', 'COUNT', 'CRASHES_PER_MONTH', 'INJURY_SCORE', 'AVERAGE_INJURY_SCORE']
        
        # Get top results
        ranking = ranking.head(limit)
        ranking = ranking.reset_index(drop=True)
        
        # Filter to only relevant columns that exist
        available_cols = [col for col in result_cols if col in ranking.columns]
        result = ranking[available_cols].to_dict(orient="records")
        
        return {
            "ranking": result,
            "rank_type": rank_type,
            "group_by": group_by,
            "total_crashes": len(df)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/data/sample")
def get_sample(limit: int = 10):
    """Return a sample of rows from the CSV"""
    try:
        df = get_dataframe()
        sample = df.head(limit)
        return {"data": sample.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/columns")
def get_columns():
    """Return column names from the CSV"""
    try:
        df = get_dataframe()
        return {"columns": df.columns.tolist()}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
