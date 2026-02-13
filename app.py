"""
Gradio UI for Football Match Analysis using Google ADK.

This app analyzes football matches using data from football-data.org API.
The LLM agent generates insights and tactical recommendations based on
pre-calculated statistics.
"""

import gradio as gr
import asyncio
import json
from dotenv import load_dotenv
from google.genai import types

# Import football tools and agent
from bi_agent.football_tools import (
    get_team_analysis,
    get_competitions,
    get_team_names_for_dropdown,
)
from bi_agent.football_agent import football_runner

# Load environment variables
load_dotenv()


async def run_football_analysis_async(team_a_data: dict, team_b_data: dict):
    """
    Run the football analysis agent with pre-calculated team data.

    Args:
        team_a_data: Analysis data for Team A (from get_team_analysis)
        team_b_data: Analysis data for Team B (from get_team_analysis)

    Returns:
        Analysis result from the LLM agent
    """
    # Create session for football analysis
    session = await football_runner.session_service.create_session(
        user_id='user',
        app_name='football_analysis'
    )

    # Prepare structured input for the LLM
    input_data = {
        "team_a": {
            "team_name": team_a_data["team_name"],
            "metrics": team_a_data["metrics"]
        },
        "team_b": {
            "team_name": team_b_data["team_name"],
            "metrics": team_b_data["metrics"]
        }
    }

    # Create user message with the structured data
    content = types.Content(
        role='user',
        parts=[types.Part(text=f"Analyze this match data:\n{json.dumps(input_data, indent=2)}")]
    )

    # Run the analysis agent
    events_async = football_runner.run_async(
        user_id='user',
        session_id=session.id,
        new_message=content
    )

    # Extract results
    result = ""
    async for event in events_async:
        if event.actions and event.actions.state_delta:
            if "analysis_result" in event.actions.state_delta:
                result = event.actions.state_delta["analysis_result"]

    return result


def update_team_dropdown(competition: str):
    """
    Update team dropdown when competition is selected.

    Args:
        competition: Selected competition display name

    Returns:
        Updated Gradio Dropdown with team choices
    """
    if not competition:
        return gr.Dropdown(choices=[], value=None)

    teams = get_team_names_for_dropdown(competition)

    # Check for errors
    if teams and teams[0].startswith("Error:"):
        return gr.Dropdown(choices=[], value=None, label=teams[0])

    return gr.Dropdown(choices=teams, value=None)


def analyze_football_match(
    league_a: str, team_a: str,
    league_b: str, team_b: str,
    num_matches: int
):
    """
    Analyze a football match between two teams.

    Args:
        league_a: Competition for Team A
        team_a: Name of Team A
        league_b: Competition for Team B
        team_b: Name of Team B
        num_matches: Number of recent matches to analyze

    Returns:
        Markdown-formatted analysis report
    """
    try:
        # Validate inputs
        if not league_a or not team_a:
            return "**Error:** Please select a league and team for Team A."
        if not league_b or not team_b:
            return "**Error:** Please select a league and team for Team B."

        # Fetch and analyze Team A
        team_a_data = get_team_analysis(team_a, league_a, num_matches)
        if not team_a_data["success"]:
            return f"**Error for Team A ({team_a}):** {team_a_data['error']}"

        # Fetch and analyze Team B
        team_b_data = get_team_analysis(team_b, league_b, num_matches)
        if not team_b_data["success"]:
            return f"**Error for Team B ({team_b}):** {team_b_data['error']}"

        # Build the report header with metrics
        report = f"""## Football Match Analysis

### {team_a_data['team_name']} vs {team_b_data['team_name']}

---

### Team Statistics (Last {num_matches} Matches)

| Metric | {team_a_data['team_name']} | {team_b_data['team_name']} |
|--------|------------|------------|
| Matches Played | {team_a_data['metrics']['matches_played']} | {team_b_data['metrics']['matches_played']} |
| Wins / Draws / Losses | {team_a_data['metrics']['wins']}/{team_a_data['metrics']['draws']}/{team_a_data['metrics']['losses']} | {team_b_data['metrics']['wins']}/{team_b_data['metrics']['draws']}/{team_b_data['metrics']['losses']} |
| Total Points | {team_a_data['metrics']['total_points']} | {team_b_data['metrics']['total_points']} |
| Goals Scored | {team_a_data['metrics']['goals_scored']} | {team_b_data['metrics']['goals_scored']} |
| Goals Conceded | {team_a_data['metrics']['goals_conceded']} | {team_b_data['metrics']['goals_conceded']} |
| Avg Goals Scored | {team_a_data['metrics']['avg_goals_scored']} | {team_b_data['metrics']['avg_goals_scored']} |
| Avg Goals Conceded | {team_a_data['metrics']['avg_goals_conceded']} | {team_b_data['metrics']['avg_goals_conceded']} |

---

### AI Analysis

"""

        # Run the LLM analysis with pre-calculated metrics
        analysis_result = asyncio.run(run_football_analysis_async(team_a_data, team_b_data))

        report += analysis_result

        return report

    except Exception as e:
        return f"**Error:** {str(e)}"


# ============================================================================
# Gradio UI
# ============================================================================

# Get list of competitions for dropdowns
COMPETITIONS = get_competitions()

with gr.Blocks(title="Football Match Analysis") as demo:
    gr.Markdown("""
    # Football Match Analysis (Google ADK)

    Analyze recent performance of two football teams using data from **football-data.org**.

    **How to use:**
    1. Select a league for each team
    2. Select the team from the dropdown
    3. Choose how many recent matches to analyze
    4. Click "Analyze Match"

    **Note:** Requires `FOOTBALL_API_KEY` in your `.env` file.
    Get a free API key at [football-data.org](https://www.football-data.org/)
    """)

    # Team A Selection
    gr.Markdown("### Team A")
    with gr.Row():
        league_a_dropdown = gr.Dropdown(
            choices=COMPETITIONS,
            label="League",
            value=None,
            scale=1
        )
        team_a_dropdown = gr.Dropdown(
            choices=[],
            label="Team",
            value=None,
            scale=2
        )

    # Team B Selection
    gr.Markdown("### Team B")
    with gr.Row():
        league_b_dropdown = gr.Dropdown(
            choices=COMPETITIONS,
            label="League",
            value=None,
            scale=1
        )
        team_b_dropdown = gr.Dropdown(
            choices=[],
            label="Team",
            value=None,
            scale=2
        )

    # Settings
    with gr.Row():
        num_matches_slider = gr.Slider(
            minimum=3,
            maximum=10,
            value=5,
            step=1,
            label="Number of Recent Matches to Analyze"
        )

    with gr.Row():
        submit_btn = gr.Button("Analyze Match", variant="primary", size="lg")

    gr.Markdown("## Analysis Report")

    output = gr.Markdown(
        value="*Select leagues and teams, then click 'Analyze Match'*"
    )

    # Event handlers: Update team dropdowns when league is selected
    league_a_dropdown.change(
        fn=update_team_dropdown,
        inputs=[league_a_dropdown],
        outputs=[team_a_dropdown]
    )

    league_b_dropdown.change(
        fn=update_team_dropdown,
        inputs=[league_b_dropdown],
        outputs=[team_b_dropdown]
    )

    # Analyze button
    submit_btn.click(
        fn=analyze_football_match,
        inputs=[league_a_dropdown, team_a_dropdown, league_b_dropdown, team_b_dropdown, num_matches_slider],
        outputs=[output]
    )


if __name__ == "__main__":
    demo.launch()
