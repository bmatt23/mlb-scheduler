import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from helpers import find_team_itineraries, itineraries_to_dataframe, team_stadium_coords, build_games_lookup

df_dist = pd.read_excel("mlb_distances.xlsx")

# Build distances dictionary
distances_between_stadiums = {}
for _, row in df_dist.iterrows():
    team1 = row['Team 1']
    team2 = row['Team 2']
    miles = row['Distance (miles)']
    # store both (team1, team2) and (team2, team1)
    distances_between_stadiums[(team1, team2)] = miles
    distances_between_stadiums[(team2, team1)] = miles



raw_df = pd.read_excel("mlb_schedule_2025_for_reddit.xlsx", header=1)
games_df = build_games_lookup(raw_df)
games_df["Date"] = pd.to_datetime(games_df["Date"])
st.title("MLB Itinerary Finder")

st.sidebar.header("Trip Filters")
selected_teams = st.sidebar.multiselect("Teams you want to see", sorted(games_df["Team"].unique()))
selected_days = st.sidebar.multiselect("Preferred days of the week", 
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
months = ["All Months", "March", "April", "May", "June", "July", "August", "September", "October"]
selected_month = st.selectbox("Filter by month", months)
max_span = st.sidebar.slider("Max number of days", 1, 14, len(selected_teams) or 3)

home_teams = st.sidebar.multiselect("Must be home team", selected_teams)
away_teams = st.sidebar.multiselect("Must be away team", selected_teams)

if selected_month != "All Months":
    games_df = games_df[games_df["Date"].dt.month_name() == selected_month]


if 'results' not in st.session_state:
    st.session_state.results = None

if st.sidebar.button("Find Itineraries"):
    if not selected_teams:
        st.warning("Please select at least one team.")
        st.session_state.results = None
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
            st.session_state.results = None
        else:
            st.session_state.results = results

if st.session_state.results:
    df = itineraries_to_dataframe(st.session_state.results)
    df["Itinerary"] = df.groupby(["Start Date", "End Date"]).ngroup()

    st.success(f"Found {len(st.session_state.results)} possible itineraries.")

    selected_itinerary = st.number_input("Which itinerary to view?", 
                                         min_value=0, 
                                         max_value=df['Itinerary'].max(), 
                                         value=0)

    df_selected = df[df["Itinerary"] == selected_itinerary].sort_values(by="Date", ascending=True)
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



    total_distance = 0
    distances_text = ""

    stadiums_in_route = [team_stadium_coords[team][0] for team in df_selected["Team"]]

    for i in range(len(stadiums_in_route) - 1):
        stadium1 = stadiums_in_route[i]
        stadium2 = stadiums_in_route[i + 1]
        miles = distances_between_stadiums.get((stadium1, stadium2), 0)
        total_distance += miles
        distances_text += f"{stadium1} to {stadium2}: {miles} miles\n"

    st.markdown(f"**Total distance:** {total_distance} miles")
    st.text(distances_text)


