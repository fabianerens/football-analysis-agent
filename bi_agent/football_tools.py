"""
Football data tools using football-data.org API.

This module provides functions to fetch and analyze football match data.
All API requests require an API key from https://www.football-data.org/

IMPORTANT: API Key Configuration
--------------------------------
The API key must be stored in an environment variable: FOOTBALL_API_KEY
It is loaded using python-dotenv from the .env file.
Every request includes the header: "X-Auth-Token": <FOOTBALL_API_KEY>

API Documentation: https://www.football-data.org/documentation/api
"""

import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
# -----------------
# Base URL for football-data.org API v4
FOOTBALL_API_BASE_URL = "https://api.football-data.org/v4"

# API key is read from environment variable - NEVER hardcode it
# The key must be set in .env file as: FOOTBALL_API_KEY=your_key_here
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

# Supported competitions in the free tier
# Format: {code: display_name}
SUPPORTED_COMPETITIONS = {
    "PL": "Premier League (England)",
    "BL1": "Bundesliga (Germany)",
    "SA": "Serie A (Italy)",
    "PD": "La Liga (Spain)",
    "FL1": "Ligue 1 (France)",
    "CL": "Champions League",
}

# Cache for teams per competition (to avoid repeated API calls)
_teams_cache: Dict[str, List[Dict]] = {}


def _get_headers() -> Dict[str, str]:
    """
    Get HTTP headers for API requests.

    The X-Auth-Token header is required for all API requests.
    The API key is loaded from the FOOTBALL_API_KEY environment variable.

    Returns:
        Dictionary with required headers including the auth token.

    Raises:
        ValueError: If FOOTBALL_API_KEY is not set.
    """
    if not FOOTBALL_API_KEY:
        raise ValueError(
            "FOOTBALL_API_KEY environment variable is not set. "
            "Please add it to your .env file: FOOTBALL_API_KEY=your_key_here"
        )

    return {
        "X-Auth-Token": FOOTBALL_API_KEY,
        "Content-Type": "application/json"
    }


def get_competitions() -> List[str]:
    """
    Get list of supported competition display names for dropdown.

    Returns:
        List of competition names (e.g., ["Premier League (England)", ...])
    """
    return list(SUPPORTED_COMPETITIONS.values())


def get_competition_code(display_name: str) -> Optional[str]:
    """
    Get competition code from display name.

    Args:
        display_name: The display name (e.g., "Premier League (England)")

    Returns:
        Competition code (e.g., "PL") or None if not found
    """
    for code, name in SUPPORTED_COMPETITIONS.items():
        if name == display_name:
            return code
    return None


def get_teams_for_competition(competition_code: str) -> Dict[str, Any]:
    """
    Get all teams for a specific competition.

    Uses caching to avoid repeated API calls (rate limiting).

    Args:
        competition_code: The competition code (e.g., "PL", "BL1")

    Returns:
        Dictionary with:
            - success: Boolean
            - teams: List of {id, name} dictionaries
            - error: Error message if failed
    """
    # Check cache first
    if competition_code in _teams_cache:
        return {
            "success": True,
            "teams": _teams_cache[competition_code],
            "error": None
        }

    try:
        headers = _get_headers()
        url = f"{FOOTBALL_API_BASE_URL}/competitions/{competition_code}/teams"

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 401:
            return {"success": False, "teams": [], "error": "Invalid API key."}
        elif response.status_code == 429:
            return {"success": False, "teams": [], "error": "Rate limit exceeded. Please wait a moment."}
        elif response.status_code != 200:
            return {"success": False, "teams": [], "error": f"API error: {response.status_code}"}

        data = response.json()
        raw_teams = data.get("teams", [])

        # Extract relevant info and sort by name
        teams = [
            {"id": t["id"], "name": t["name"]}
            for t in raw_teams
        ]
        teams.sort(key=lambda x: x["name"])

        # Cache the result
        _teams_cache[competition_code] = teams

        return {
            "success": True,
            "teams": teams,
            "error": None
        }

    except ValueError as e:
        return {"success": False, "teams": [], "error": str(e)}
    except requests.exceptions.RequestException as e:
        return {"success": False, "teams": [], "error": f"Network error: {str(e)}"}


def get_team_names_for_dropdown(competition_display_name: str) -> List[str]:
    """
    Get list of team names for a competition (for Gradio dropdown).

    Args:
        competition_display_name: Display name of competition

    Returns:
        List of team names, or ["Error: ..."] if failed
    """
    code = get_competition_code(competition_display_name)
    if not code:
        return ["Error: Unknown competition"]

    result = get_teams_for_competition(code)
    if not result["success"]:
        return [f"Error: {result['error']}"]

    return [t["name"] for t in result["teams"]]


def get_team_id_by_name(team_name: str, competition_code: str) -> Optional[int]:
    """
    Get team ID by name from cached data.

    Args:
        team_name: The team name
        competition_code: The competition code

    Returns:
        Team ID or None if not found
    """
    if competition_code not in _teams_cache:
        # Fetch if not cached
        get_teams_for_competition(competition_code)

    if competition_code in _teams_cache:
        for team in _teams_cache[competition_code]:
            if team["name"] == team_name:
                return team["id"]

    return None


def get_recent_matches(team_id: int, limit: int = 5) -> Dict[str, Any]:
    """
    Get recent finished matches for a team.

    Args:
        team_id: The team ID from football-data.org
        limit: Number of recent matches to fetch (default: 5)

    Returns:
        Dictionary with:
            - success: Boolean indicating if request succeeded
            - matches: List of match dictionaries (if success)
            - error: Error message (if failed)

        Each match contains:
            - date: Match date
            - home_team: Home team name
            - away_team: Away team name
            - home_score: Goals scored by home team
            - away_score: Goals scored by away team
            - is_home: Whether the requested team played at home
    """
    try:
        headers = _get_headers()

        # Get finished matches for the team
        url = f"{FOOTBALL_API_BASE_URL}/teams/{team_id}/matches"
        params = {
            "status": "FINISHED",
            "limit": limit
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        # Handle HTTP errors
        if response.status_code == 401:
            return {"success": False, "matches": [], "error": "Invalid API key."}
        elif response.status_code == 404:
            return {"success": False, "matches": [], "error": f"Team with ID {team_id} not found."}
        elif response.status_code != 200:
            return {"success": False, "matches": [], "error": f"API error: {response.status_code}"}

        data = response.json()
        raw_matches = data.get("matches", [])

        # Process matches into a cleaner format
        matches = []
        for match in raw_matches[:limit]:
            home_team = match.get("homeTeam", {})
            away_team = match.get("awayTeam", {})
            score = match.get("score", {}).get("fullTime", {})

            matches.append({
                "date": match.get("utcDate", ""),
                "home_team": home_team.get("name", "Unknown"),
                "away_team": away_team.get("name", "Unknown"),
                "home_score": score.get("home", 0),
                "away_score": score.get("away", 0),
                "is_home": home_team.get("id") == team_id
            })

        return {
            "success": True,
            "matches": matches,
            "error": None
        }

    except ValueError as e:
        return {"success": False, "matches": [], "error": str(e)}
    except requests.exceptions.RequestException as e:
        return {"success": False, "matches": [], "error": f"Network error: {str(e)}"}


def calculate_metrics(matches: List[Dict], team_name: str) -> Dict[str, Any]:
    """
    Calculate performance metrics from match data.

    This function performs all statistical calculations in Python,
    so the LLM only receives structured results and doesn't need
    to perform arithmetic.

    Args:
        matches: List of match dictionaries from get_recent_matches()
        team_name: Name of the team to calculate metrics for

    Returns:
        Dictionary with calculated metrics:
            - matches_played: Number of matches analyzed
            - avg_goals_scored: Average goals scored per match
            - avg_goals_conceded: Average goals conceded per match
            - total_points: Total points earned (3 for win, 1 for draw, 0 for loss)
            - wins: Number of wins
            - draws: Number of draws
            - losses: Number of losses
            - goals_scored: Total goals scored
            - goals_conceded: Total goals conceded
    """
    if not matches:
        return {
            "matches_played": 0,
            "avg_goals_scored": 0.0,
            "avg_goals_conceded": 0.0,
            "total_points": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_scored": 0,
            "goals_conceded": 0
        }

    goals_scored = 0
    goals_conceded = 0
    wins = 0
    draws = 0
    losses = 0

    for match in matches:
        home_score = match.get("home_score", 0) or 0
        away_score = match.get("away_score", 0) or 0
        is_home = match.get("is_home", True)

        # Calculate goals for this team
        if is_home:
            team_goals = home_score
            opponent_goals = away_score
        else:
            team_goals = away_score
            opponent_goals = home_score

        goals_scored += team_goals
        goals_conceded += opponent_goals

        # Determine match result
        if team_goals > opponent_goals:
            wins += 1
        elif team_goals == opponent_goals:
            draws += 1
        else:
            losses += 1

    matches_played = len(matches)
    total_points = (wins * 3) + (draws * 1)

    return {
        "matches_played": matches_played,
        "avg_goals_scored": round(goals_scored / matches_played, 2),
        "avg_goals_conceded": round(goals_conceded / matches_played, 2),
        "total_points": total_points,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded
    }


def get_team_analysis(team_name: str, competition_display_name: str, num_matches: int = 5) -> Dict[str, Any]:
    """
    Get complete analysis data for a team.

    This function fetches match data and calculates metrics.

    Args:
        team_name: Name of the team (from dropdown)
        competition_display_name: Competition display name (from dropdown)
        num_matches: Number of recent matches to analyze

    Returns:
        Dictionary with:
            - success: Boolean indicating if analysis succeeded
            - team_name: Official team name
            - matches: List of recent matches
            - metrics: Calculated performance metrics
            - error: Error message (if failed)
    """
    # Step 1: Get competition code
    competition_code = get_competition_code(competition_display_name)
    if not competition_code:
        return {
            "success": False,
            "team_name": team_name,
            "matches": [],
            "metrics": {},
            "error": f"Unknown competition: {competition_display_name}"
        }

    # Step 2: Get team ID from cache
    team_id = get_team_id_by_name(team_name, competition_code)
    if not team_id:
        return {
            "success": False,
            "team_name": team_name,
            "matches": [],
            "metrics": {},
            "error": f"Team '{team_name}' not found in {competition_display_name}"
        }

    # Step 3: Get recent matches
    matches_result = get_recent_matches(team_id, limit=num_matches)
    if not matches_result["success"]:
        return {
            "success": False,
            "team_name": team_name,
            "matches": [],
            "metrics": {},
            "error": matches_result["error"]
        }

    matches = matches_result["matches"]

    # Step 4: Calculate metrics (done in Python, not by LLM)
    metrics = calculate_metrics(matches, team_name)

    return {
        "success": True,
        "team_name": team_name,
        "matches": matches,
        "metrics": metrics,
        "error": None
    }
