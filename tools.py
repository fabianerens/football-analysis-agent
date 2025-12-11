"""
Tools for the Business Intelligence agents.

This module defines tools that agents can call to interact with the database,
execute queries, and process results.
"""

import pandas as pd
from typing import Dict, Any
from db_config import create_db_engine
from sql_executor import execute_query, validate_sql


class DatabaseTools:
    """Tools for database operations that agents can use."""

    def __init__(self, server: str, database: str, username: str, password: str):
        """
        Initialize database tools with connection credentials.

        Args:
            server: SQL Server hostname
            database: Database name
            username: Database username
            password: Database password
        """
        self.engine = create_db_engine(server, database, username, password)

    def execute_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query and return the results.

        This tool validates and executes SQL queries against the database.
        Only SELECT queries are allowed for safety.

        Args:
            sql_query: The SQL query to execute

        Returns:
            Dictionary containing:
                - success: Boolean indicating if query succeeded
                - data: List of dictionaries with query results
                - columns: List of column names
                - row_count: Number of rows returned
                - error: Error message if query failed
        """
        # Validate and execute the query
        result = execute_query(self.engine, sql_query)

        if result['success']:
            # Convert DataFrame to list of dicts for JSON serialization
            df = result['data']
            data_list = df.to_dict(orient='records') if df is not None else []

            return {
                'success': True,
                'data': data_list,
                'columns': result['columns'],
                'row_count': result['row_count'],
                'error': None
            }
        else:
            return {
                'success': False,
                'data': [],
                'columns': [],
                'row_count': 0,
                'error': result['error']
            }
