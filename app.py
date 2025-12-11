"""
Gradio UI for the Business Intelligence Agent Pipeline.

This app demonstrates Google ADK's SequentialAgent pattern:
1. Text-to-SQL Agent (standalone)
2. SQL execution via BIService
3. Insight Pipeline (SequentialAgent: Visualization → Explanation)
"""

import gradio as gr
import asyncio
import os
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from google.genai import types

# Import agents and BI service
from agents import text_to_sql_runner, insight_runner
from bi_service import BIService

load_dotenv()


# Load default database credentials from environment
DEFAULT_SERVER = os.getenv("MSSQL_SERVER", "")
DEFAULT_DATABASE = os.getenv("MSSQL_DATABASE", "")
DEFAULT_USERNAME = os.getenv("MSSQL_USERNAME", "")
DEFAULT_PASSWORD = os.getenv("MSSQL_PASSWORD", "")


async def call_agent_async(runner, message_text, app_name='agent'):
    """Helper function to call an agent/pipeline and extract results."""
    session = await runner.session_service.create_session(user_id='user', app_name=app_name)

    content = types.Content(
        role='user',
        parts=[types.Part(text=message_text)]
    )

    events_async = runner.run_async(
        user_id='user',
        session_id=session.id,
        new_message=content
    )

    results = {}
    async for event in events_async:
        if event.actions and event.actions.state_delta:
            for key, value in event.actions.state_delta.items():
                results[key] = value

    return results


async def process_request_async(
    message: str,
    server: str,
    database: str,
    username: str,
    password: str
):
    """
    Process user request through the BI pipeline.

    Pipeline:
    1. Text-to-SQL Agent → Generates SQL
    2. BIService → Executes SQL
    3. Insight Pipeline (SequentialAgent) → Visualization + Explanation
    """
    try:
        # Validate inputs
        if not message.strip():
            return "Error: Please enter a question", None, None, "Error: No question provided"

        if not all([server, database, username, password]):
            return "Error: Missing database credentials", None, None, "Error: Please provide all database connection details"

        # ====================================================================
        # Initialize BI Service
        # ====================================================================
        bi_service = BIService(server, database, username, password)

        # Connect to database
        is_connected, conn_message = bi_service.connect()
        if not is_connected:
            return f"Error: {conn_message}", None, None, "Error: Could not connect to database"

        # Load database schema
        try:
            bi_service.load_schema(max_tables=20)
        except Exception as e:
            return f"Error retrieving schema: {str(e)}", None, None, "Error: Could not retrieve database schema"

        # ====================================================================
        # Step 1: Call Text-to-SQL Agent
        # ====================================================================
        sql_prompt = bi_service.get_schema_for_sql_generation(message)
        sql_results = await call_agent_async(text_to_sql_runner, sql_prompt, 'text_to_sql')
        sql_query = sql_results.get('sql_query', '')

        # Clean up SQL query
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()

        # ====================================================================
        # Step 2: Execute SQL Query via BI Service
        # ====================================================================
        result = bi_service.execute_sql(sql_query)

        if not result['success']:
            error_msg = result['error']
            sql_query = f"-- Error executing query\n{sql_query}\n\n-- Error: {error_msg}"
            bi_service.close()
            return sql_query, None, None, f"Error executing query: {error_msg}"

        df = result['data']

        if df.empty:
            bi_service.close()
            return sql_query, df, None, "The query executed successfully but returned no data."

        # ====================================================================
        # Step 3: Call Insight Pipeline (SequentialAgent)
        # Pipeline: Visualization Agent → Explanation Agent
        # ====================================================================
        chart = None
        explanation_text = ""

        try:
            # Prepare data for insight agents
            insight_prompt = bi_service.prepare_data_for_agents(df, sql_query)
            insight_prompt += "\n\nPlease generate a visualization and explanation for this data."

            # Call the insight pipeline (SequentialAgent)
            insight_results = await call_agent_async(insight_runner, insight_prompt, 'insights')

            # Extract results
            chart_spec = insight_results.get('chart_spec', '')
            explanation_text = insight_results.get('explanation_text', '')

            # Execute chart specification
            if chart_spec:
                chart_spec_clean = chart_spec.strip()
                if chart_spec_clean.startswith("```python"):
                    chart_spec_clean = chart_spec_clean.replace("```python", "").replace("```", "").strip()
                elif chart_spec_clean.startswith("```"):
                    chart_spec_clean = chart_spec_clean.replace("```", "").strip()

                # Create namespace and execute chart code
                namespace = {
                    'alt': alt,
                    'pd': pd,
                    'df': df,
                    'data': df.to_dict(orient='records')
                }

                exec(chart_spec_clean, namespace)

                if 'chart' in namespace:
                    chart = namespace['chart']

        except Exception as e:
            print(f"Insight pipeline error: {str(e)}")
            import traceback
            traceback.print_exc()
            explanation_text = "Unable to generate insights."

        # Clean up
        bi_service.close()

        # Return all four outputs
        return sql_query, df, chart, explanation_text

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Full error: {e}")
        import traceback
        traceback.print_exc()
        return error_msg, None, None, error_msg


def process_request(message: str, server: str, database: str, username: str, password: str):
    """Synchronous wrapper for Gradio."""
    try:
        sql_query, df, chart, explanation = asyncio.run(
            process_request_async(message, server, database, username, password)
        )
        return sql_query, df, chart, explanation
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return error_msg, None, None, error_msg


# ============================================================================
# Gradio UI
# ============================================================================

with gr.Blocks(title="Business Intelligence Agent") as demo:
    gr.Markdown("""
    # Business Intelligence Agent (Google ADK)

    This demo uses **Google ADK's SequentialAgent pattern**:

    1. **Text-to-SQL Agent** → Generates SQL from natural language
    2. **BI Service** → Executes SQL against database
    3. **Insight Pipeline** (**SequentialAgent**) → Visualization Agent → Explanation Agent

    Enter your question below and click "Analyze Data".
    """)

    with gr.Row():
        user_input = gr.Textbox(
            label="Your Question",
            placeholder="e.g., 'What are the top 10 products by price?'",
            lines=3
        )

    # Database configuration
    with gr.Accordion("Database Configuration", open=False):
        gr.Markdown("Configure your SQL Server connection details:")

        with gr.Row():
            server_input = gr.Textbox(
                label="Server",
                value=DEFAULT_SERVER,
                placeholder="e.g., dwh.hdm-server.eu"
            )
            database_input = gr.Textbox(
                label="Database",
                value=DEFAULT_DATABASE,
                placeholder="e.g., AdventureBikes Sales DataMart"
            )

        with gr.Row():
            username_input = gr.Textbox(
                label="Username",
                value=DEFAULT_USERNAME,
                placeholder="Database username"
            )
            password_input = gr.Textbox(
                label="Password",
                value=DEFAULT_PASSWORD,
                type="password",
                placeholder="Database password"
            )

    with gr.Row():
        submit_btn = gr.Button("Analyze Data", variant="primary")
        clear_btn = gr.Button("Clear")

    gr.Markdown("## Results")

    # Four output panels
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Generated SQL")
            sql_output = gr.Code(
                label="SQL Query",
                language="sql",
                value="-- Waiting for input..."
            )

        with gr.Column(scale=1):
            gr.Markdown("### Query Results")
            data_output = gr.DataFrame(
                label="Data Table",
                wrap=True
            )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Visualization")
            chart_output = gr.Plot(label="Chart")

        with gr.Column(scale=1):
            gr.Markdown("### Insights")
            explanation_output = gr.Markdown(
                value="*Waiting for input...*"
            )

    # Examples
    gr.Examples(
        examples=[
            ["What are the top 10 products by transfer price?"],
            ["Show me the product categories and their average prices"],
            ["List all products in the Bikes category"],
            ["How many products are there in each category?"],
            ["What is the most expensive product?"],
        ],
        inputs=user_input
    )

    # Button actions
    submit_btn.click(
        fn=process_request,
        inputs=[user_input, server_input, database_input, username_input, password_input],
        outputs=[sql_output, data_output, chart_output, explanation_output]
    )

    clear_btn.click(
        fn=lambda: (
            "",
            "-- Waiting for input...",
            None,
            None,
            "*Waiting for input...*"
        ),
        inputs=None,
        outputs=[user_input, sql_output, data_output, chart_output, explanation_output]
    )


if __name__ == "__main__":
    demo.launch()
