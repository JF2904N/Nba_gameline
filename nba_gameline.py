#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 11:26:38 2025

@author: jf
"""


from nba_api.stats.endpoints import teamplayerdashboard, leaguedashteamstats, teamdashboardbygeneralsplits
from nba_api.stats.static import teams
import time
from datetime import datetime

# Function to determine the current season
def get_current_season():
    current_year = datetime.now().year
    current_month = datetime.now().month
    if current_month >= 10:  # NBA season starts in October
        return f"{current_year}-{str(current_year + 1)[-2:]}"
    else:
        return f"{current_year - 1}-{str(current_year)[-2:]}"


# Function to get team ID based on user input
def get_team_id(team_name):
    all_teams = teams.get_teams()
    team = [team for team in all_teams if team['full_name'].lower() == team_name.lower()]
    return team[0]['id'] if team else None


# Function to fetch team stats
def fetch_team_avg_points_per_game(team_id, season):
    try:
        time.sleep(1)  # Avoid throttling
        team_dashboard = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(team_id=team_id, season=season)
        overall_stats = team_dashboard.get_normalized_dict()['OverallTeamDashboard'][0]
        total_points = overall_stats['PTS']
        games_played = overall_stats['GP']
        return total_points / games_played, overall_stats
    except Exception as e:
        print(f"Error fetching team stats: {e}")
        return 0, None


# Function to fetch player stats and calculate total average points (excluding injured players)
def fetch_player_avg_points(team_id, season):
    try:
        time.sleep(1)  # Avoid throttling
        player_dashboard = teamplayerdashboard.TeamPlayerDashboard(team_id=team_id, season=season)
        player_stats = player_dashboard.get_data_frames()[1]  # Player stats DataFrame

        # Calculate PPG for each player
        player_stats['PPG'] = player_stats['PTS'] / player_stats['GP']

        # Exclude injured players (assume players with 0 GP are injured)
        active_players = player_stats[player_stats['GP'] > 0]

        # Include rebounds per game (REB) and assists per game (AST)
        active_players['RPG'] = active_players['REB'] / active_players['GP']
        active_players['APG'] = active_players['AST'] / active_players['GP']

        # Sum up the PPG for all active players to get the team's total player points per game
        total_player_ppg = active_players['PPG'].sum()

        # Return the total PPG and a filtered DataFrame with desired stats
        return total_player_ppg, active_players[['PLAYER_NAME', 'PPG', 'RPG', 'APG']]
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        return 0, None



# Function to fetch team record and win percentage
def fetch_team_record(team_id, season):
    try:
        time.sleep(1)  # Avoid throttling
        team_stats = leaguedashteamstats.LeagueDashTeamStats(season=season)
        team_stats_df = team_stats.get_data_frames()[0]
        team_row = team_stats_df[team_stats_df['TEAM_ID'] == team_id]
        if not team_row.empty:
            return team_row.iloc[0]['W_PCT'], team_row
    except Exception as e:
        print(f"Error fetching team record: {e}")
    return 0, None


# Main function to predict game outcome
def predict_game():
    season = get_current_season()
    print(f"Fetching data for the {season} season...\n")

    # Input team names and home court advantage
    home_team = input("Enter the home team name: ")
    away_team = input("Enter the away team name: ")


    team1_id = get_team_id(home_team)
    team2_id = get_team_id(away_team)

    if not team1_id or not team2_id:
        print("One or both teams not found. Please check the spelling and try again.")
        return

    # Fetch data for both teams
    print("\nFetching data for both teams...\n")

    # Fetch and display team average points per game
    team1_avg_ppg, _ = fetch_team_avg_points_per_game(team1_id, season)
    team2_avg_ppg, _ = fetch_team_avg_points_per_game(team2_id, season)
    print(f"{home_team} Average Points Per Game: {team1_avg_ppg:.2f}")
    print(f"{away_team} Average Points Per Game: {team2_avg_ppg:.2f}")

    # Fetch and display player stats
    team1_player_avg_ppg, team1_player_stats = fetch_player_avg_points(team1_id, season)
    team2_player_avg_ppg, team2_player_stats = fetch_player_avg_points(team2_id, season)
    print(f"\n{home_team} Player Stats:\n", team1_player_stats)
    print(f"\n{away_team} Player Stats:\n", team2_player_stats)

    # Fetch and display team records
    team1_record, _ = fetch_team_record(team1_id, season)
    team2_record, _ = fetch_team_record(team2_id, season)
    print(f"\n{home_team} Win Percentage: {team1_record:.2%}")
    print(f"{away_team} Win Percentage: {team2_record:.2%}")

    # Calculate points
    team1_points = 0.5
    team2_points = 0

    # Rule 1: Team current total points per game average
    if team1_avg_ppg > team2_avg_ppg:
        team1_points += 1
    else:
        team2_points += 1

    # Rule 2: Player average points in the team
    if team1_player_avg_ppg > team2_player_avg_ppg:
        team1_points += 1
    else:
        team2_points += 1

    # Rule 3: Team record
    if team1_record > team2_record:
        team1_points += 1
    else:
        team2_points += 1


    # Print results
    print(f"\nResults:")
    print(f"{home_team} Points: {team1_points}")
    print(f"{away_team} Points: {team2_points}")

    if team1_points > team2_points:
        print(f"\nPrediction: {home_team} wins!")
    elif team2_points > team1_points:
        print(f"\nPrediction: {away_team} wins!")
    else:
        print("\nPrediction: It's a tie!")


if __name__ == "__main__":
    predict_game()
