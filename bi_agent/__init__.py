"""
Agent Package for Google ADK.

Contains:
- Football Match Analysis (main app) - uses football-data.org API
- Business Intelligence agents (legacy, for adk web compatibility)
"""

from bi_agent.agent import (
    # Root agent (main entry point for ADK web)
    root_agent,
    root_runner,
    # Individual agents
    text_to_sql_agent,
    text_to_sql_runner,
    sql_executor_agent,
    data_formatter_agent,
    visualization_agent,
    explanation_agent,
    # Pipelines
    insight_pipeline,
    insight_runner,
    # Constants
    GEMINI_MODEL
)

from bi_agent.tools import DatabaseTools, execute_sql_and_format, get_database_schema

# Football analysis components
from bi_agent.football_tools import (
    get_recent_matches,
    calculate_metrics,
    get_team_analysis,
    get_competitions,
    get_team_names_for_dropdown,
    get_teams_for_competition,
    SUPPORTED_COMPETITIONS
)
from bi_agent.football_agent import football_analysis_agent, football_runner

__all__ = [
    # Root agent (required for ADK web)
    'root_agent',
    'root_runner',
    # Individual agents
    'text_to_sql_agent',
    'text_to_sql_runner',
    'sql_executor_agent',
    'data_formatter_agent',
    'visualization_agent',
    'explanation_agent',
    # Pipelines
    'insight_pipeline',
    'insight_runner',
    # Constants
    'GEMINI_MODEL',
    # Services and Tools
    'DatabaseTools',
    'execute_sql_and_format',
    'get_database_schema',
    # Football Analysis
    'get_recent_matches',
    'calculate_metrics',
    'get_team_analysis',
    'get_competitions',
    'get_team_names_for_dropdown',
    'get_teams_for_competition',
    'SUPPORTED_COMPETITIONS',
    'football_analysis_agent',
    'football_runner',
]
