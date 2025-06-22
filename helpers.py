import pandas as pd
from itertools import permutations
from datetime import timedelta

def build_games_lookup(schedule):
    rows = []
    for _, row in schedule.iterrows():
        for team, loc in [(row["Home Team"], "Home"), (row["Away Team"], "Away")]:
            rows.append({
                "Team": team,
                "Opponent": row["Away Team"] if team == row["Home Team"] else row["Home Team"],
                "Location": loc,
                "Date": row["Game Date"],
                "Day": row["Day of Week"],
                "Stadium": row["Location"],
                "Local Time": row["Local Time"]
            })
    return pd.DataFrame(rows)


def find_team_itineraries(
    games_df,
    team_list,
    day_of_week_list=None,
    total_day_span=None,
    home_teams=None,
    away_teams=None
):
    total_day_span = total_day_span or len(team_list)
    filtered_games = games_df[games_df["Team"].isin(team_list)]

    # Optional filters
    if day_of_week_list:
        filtered_games = filtered_games[filtered_games["Day"].isin(day_of_week_list)]
    if home_teams:
        filtered_games = filtered_games[~(
            (filtered_games["Team"].isin(home_teams)) & (filtered_games["Location"] != "Home")
        )]
    if away_teams:
        filtered_games = filtered_games[~(
            (filtered_games["Team"].isin(away_teams)) & (filtered_games["Location"] != "Away")
        )]

    filtered_games = filtered_games.sort_values("Date")
    valid_itineraries = []
    unique_dates = filtered_games["Date"].unique()

    for start_date in unique_dates:
        end_date = start_date + timedelta(days=total_day_span - 1)
        window = filtered_games[
            (filtered_games["Date"] >= start_date) &
            (filtered_games["Date"] <= end_date)
        ]

        # Skip if not enough days to assign unique teams
        if window["Date"].nunique() < len(team_list):
            continue

        # Try all combinations of date assignments
        for date_combo in permutations(window["Date"].unique(), len(team_list)):
            itinerary = []
            success = True
            for team, date in zip(team_list, date_combo):
                match = window[(window["Team"] == team) & (window["Date"] == date)]
                if match.empty:
                    success = False
                    break
                row = match.iloc[0]
                itinerary.append({
                    "Team": team,
                    "Date": row["Date"],
                    "Day": row["Day"],
                    "Opponent": row["Opponent"],
                    "Location": row["Location"],
                    "Stadium": row["Stadium"],
                    "Local Time": row["Local Time"]
                })
            if success:
                valid_itineraries.append({
                    "Start Date": start_date,
                    "End Date": end_date,
                    "Games": itinerary
                })
                break  # only one result per window

    return valid_itineraries



def itineraries_to_dataframe(itineraries):
    all_rows = []

    for itin in itineraries:
        for game in itin["Games"]:
            all_rows.append({
                "Start Date": itin["Start Date"].date(),
                "End Date": itin["End Date"].date(),
                "Team": game["Team"],
                "Date": game["Date"].date(),
                "Day": game["Day"],
                "Opponent": game["Opponent"],
                "Location": game["Location"],
                "Stadium": game["Stadium"],
                "Local Time": game["Local Time"],
            })

    return pd.DataFrame(all_rows)

team_stadium_coords = {
    "D-backs": ["Chase Field - Phoenix", (33.4455, -112.0667)],
    "Braves": ["Truist Park - Atlanta", (33.8908, -84.4678)],
    "Orioles": ["Oriole Park at Camden Yards - Baltimore", (39.2839, -76.6218)],
    "Red Sox": ["Fenway Park - Boston", (42.3467, -71.0972)],
    "White Sox": ["Guaranteed Rate Field - Chicago", (41.8299, -87.6338)],
    "Cubs": ["Wrigley Field - Chicago", (41.9484, -87.6553)],
    "Reds": ["Great American Ball Park - Cincinnati", (39.0979, -84.5073)],
    "Guardians": ["Progressive Field - Cleveland", (41.4962, -81.6852)],
    "Rockies": ["Coors Field - Denver", (39.7559, -104.9942)],
    "Tigers": ["Comerica Park - Detroit", (42.3390, -83.0485)],
    "Astros": ["Minute Maid Park - Houston", (29.7573, -95.3555)],
    "Royals": ["Kauffman Stadium - Kansas City", (39.0516, -94.4803)],
    "Angels": ["Angel Stadium - Anaheim", (33.8003, -117.8827)],
    "Dodgers": ["Dodger Stadium - Los Angeles", (34.0739, -118.2400)],
    "Marlins": ["loanDepot Park - Miami", (25.7780, -80.2197)],
    "Brewers": ["American Family Field - Milwaukee", (43.0280, -87.9712)],
    "Twins": ["Target Field - Minneapolis", (44.9817, -93.2773)],
    "Mets": ["Citi Field - New York", (40.7571, -73.8458)],
    "Yankees": ["Yankee Stadium - New York", (40.8296, -73.9262)],
    "Athletics": ["Oakland Coliseum - Oakland", (37.7516, -122.2005)],
    "Phillies": ["Citizens Bank Park - Philadelphia", (39.9057, -75.1665)],
    "Pirates": ["PNC Park - Pittsburgh", (40.4469, -80.0057)],
    "Padres": ["Petco Park - San Diego", (32.7073, -117.1570)],
    "Giants": ["Oracle Park - San Francisco", (37.7786, -122.3893)],
    "Mariners": ["T-Mobile Park - Seattle", (47.5914, -122.3325)],
    "Cardinals": ["Busch Stadium - St. Louis", (38.6226, -90.1928)],
    "Rays": ["Tropicana Field - St. Petersburg", (27.7683, -82.6534)],
    "Rangers": ["Globe Life Field - Arlington", (32.7513, -97.0820)],
    "Blue Jays": ["Rogers Centre - Toronto", (43.6414, -79.3894)],
    "Nationals": ["Nationals Park - Washington", (38.8728, -77.0075)],
}
