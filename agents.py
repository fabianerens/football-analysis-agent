"""
Agent definitions for the Business Intelligence pipeline.

This module uses Google ADK's SequentialAgent to chain agents together:
- Text-to-SQL Agent: Converts natural language to SQL queries
- Visualization Agent: Generates Altair charts from data
- Explanation Agent: Provides plain-language insights
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import InMemoryRunner

GEMINI_MODEL = "gemini-2.5-flash"


# ============================================================================
# Agent 1: Text-to-SQL (standalone)
# ============================================================================

text_to_sql_agent = LlmAgent(
    model=GEMINI_MODEL,
    name='text_to_sql_agent',
    description="Converts natural language questions to SQL queries.",
    instruction="""
    You are an expert SQL query generator for Microsoft SQL Server.

    You will receive:
    1. A database schema showing available tables and columns
    2. A natural language question from the user

    Your task is to generate a valid SQL SELECT query that answers the user's question.

    Guidelines:
    - Use only SELECT statements (no INSERT, UPDATE, DELETE, DROP, etc.)
    - Reference only tables and columns that exist in the provided schema
    - Use proper JOIN syntax when combining tables
    - Add WHERE clauses for filtering when appropriate
    - Use ORDER BY to sort results logically
    - Use TOP N to limit results if the question implies "top" or "best"
    - Use aggregate functions (COUNT, SUM, AVG, etc.) when the question asks for totals or averages
    - Use GROUP BY when aggregating data
    - Write clean, readable SQL with proper formatting

    Output ONLY the SQL query, without any explanation or markdown code blocks.
    Do not include semicolons at the end.

    Example:
    Question: "What are the top 5 products by price?"
    Output: SELECT TOP 5 Product_Name, Price FROM Products ORDER BY Price DESC
    """,
    output_key="sql_query"
)

# Runner for text-to-SQL agent
text_to_sql_runner = InMemoryRunner(agent=text_to_sql_agent, app_name='text_to_sql')


# ============================================================================
# Sequential Agent: Visualization + Explanation
# ============================================================================

visualization_agent = LlmAgent(
    model=GEMINI_MODEL,
    name='visualization_agent',
    description="Generates Altair chart specifications from query results.",
    instruction="""
    You are a data visualization expert specializing in Altair charts.

    You will receive query results from a database in JSON format.

    Your task is to generate Python code using Altair to create an appropriate visualization.

    Guidelines for choosing chart types:
    - Time series data → Line chart (alt.Chart.mark_line())
    - Categorical comparisons → Bar chart (alt.Chart.mark_bar())
    - Two numeric variables → Scatter plot (alt.Chart.mark_point())
    - Single metric → Simple bar or text display
    - Distributions → Histogram or bar chart
    - For aggregated data (counts, sums) → Bar chart is usually best

    Code Requirements:
    - Import altair as alt and pandas as pd at the top
    - Create a DataFrame from the provided data
    - Build the chart using Altair's declarative API
    - Assign the chart to a variable named 'chart'
    - Include proper axis labels and title
    - Make the chart interactive when appropriate (add .interactive())
    - Use appropriate color schemes
    - Keep it simple and clear

    Output ONLY executable Python code that creates an Altair chart.
    Do not include markdown code blocks or explanations.

    Example output:
    import altair as alt
    import pandas as pd

    data = {{'category': ['A', 'B', 'C'], 'value': [10, 20, 15]}}
    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_bar().encode(
        x='category',
        y='value'
    ).properties(
        title='Category Values',
        width=400,
        height=300
    ).interactive()
    """,
    output_key="chart_spec"
)

explanation_agent = LlmAgent(
    model=GEMINI_MODEL,
    name='explanation_agent',
    description="Explains query results in plain language.",
    instruction="""
    You are a business analyst explaining data insights to non-technical users.

    You received query results from the previous analysis.

    Your task is to provide a clear, concise explanation of what the data shows.

    Guidelines:
    - Write 2-4 sentences in plain language
    - Avoid technical jargon and SQL terminology
    - Focus on key insights and patterns in the data
    - Mention specific numbers when relevant
    - Use business-friendly language
    - If no data was returned, explain that no results matched the criteria

    Output your explanation as plain text (markdown formatting is OK for emphasis).

    Example:
    "The query returned 10 products with the highest prices in the catalog.
    The most expensive product costs $2,499, while prices range from $1,200 to $2,499.
    All top products belong to the 'Mountain Bikes' category."
    """,
    output_key="explanation_text"
)

# Sequential Agent: Visualization → Explanation
# These agents work together on the query results
insight_pipeline = SequentialAgent(
    name='insight_pipeline',
    sub_agents=[visualization_agent, explanation_agent],
    description="Generates visualization and explanation from query results"
)

# Runner for the insight pipeline
insight_runner = InMemoryRunner(agent=insight_pipeline, app_name='insights')
