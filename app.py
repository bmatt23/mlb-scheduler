import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from helpers import find_team_itineraries, itineraries_to_dataframe, team_stadium_coords, build_games_lookup


raw_df = pd.read_excel("mlb_schedule_2025_for_reddit.xlsx", header=1)
games_df = build_games_lookup(raw_df)
st.title("MLB Itinerary Finder")

st.sidebar.header("Trip Filters")
selected_teams = st.sidebar.multiselect("Teams you want to see", sorted(games_df["Team"].unique()))
selected_days = st.sidebar.multiselect("Preferred days of the week", 
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
max_span = st.sidebar.slider("Max number of days", 1, 14, len(selected_teams) or 3)

home_teams = st.sidebar.multiselect("Must be home team", selected_teams)
away_teams = st.sidebar.multiselect("Must be away team", selected_teams)


if st.sidebar.button("Find Itineraries"):
    if not selected_teams:
        st.warning("Please select at least one team.")
    else:
        results = find_team_itineraries(
            games_df,
            team_list=selected_teams,
            day_of_week_list=selected_days or None,
            total_day_span=max_span,
            home_teams=home_teams or None,
            away_teams=away_teams or None
        )

        if not results:
            st.error("No itineraries found. Try loosening filters.")
        else:
            df = itineraries_to_dataframe(results)
            df["Itinerary"] = df.groupby(["Start Date", "End Date"]).ngroup()

            st.success(f"Found {len(results)} possible itineraries.")


            selected_itinerary = st.number_input("Which itinerary to view?", 
                                                 min_value=0, 
                                                 max_value=df['Itinerary'].max(), 
                                                 value=0)

            df_selected = df[df["Itinerary"] == selected_itinerary]
            st.dataframe(df_selected, use_container_width=True)


            m = folium.Map(location=[39.5, -98.35], zoom_start=4)

            route = []
            for _, row in df_selected.iterrows():
                team = row["Team"]
                stadium_name, coords = team_stadium_coords.get(team, (None, None))
                if coords:
                    route.append(coords)
                    folium.Marker(
                        coords,
                        tooltip=f"{team} ({row['Date']})",
                        popup=stadium_name
                    ).add_to(m)

            if len(route) > 1:
                folium.PolyLine(route, color="blue", weight=3).add_to(m)

            st_folium(m, width=800, height=500)
