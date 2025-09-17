from dash import html, dcc, dash_table
import pandas as pd
from config import DEFAULT_WELCOME_TITLE, DEFAULT_WELCOME_DESCRIPTION, DEFAULT_SUGGESTIONS
from utils import format_sql_query

def create_user_message(user_input):
    """Create a user message component"""
    return html.Div([
        html.Div([
            html.Div("Y", className="user-avatar"),
            html.Span("You", className="model-name")
        ], className="user-info"),
        html.Div(user_input, className="message-text")
    ], className="user-message message")

def create_thinking_indicator():
    """Create a thinking indicator component"""
    return html.Div([
        html.Div([
            html.Span(className="spinner"),
            html.Span("Thinking...")
        ], className="thinking-indicator")
    ], className="bot-message message")

def create_data_table(df, table_id):
    """Create a data table component"""
    return dash_table.DataTable(
        id=table_id,
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        
        # Other table properties
        page_size=10,
        style_table={
            'display': 'inline-block',
            'overflowX': 'auto',
            'width': '95%',
            'marginRight': '20px'
        },
        style_cell={
            'textAlign': 'left',
            'fontSize': '12px',
            'padding': '4px 10px',
            'fontFamily': '-apple-system, BlinkMacSystemFont,Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
            'backgroundColor': 'transparent',
            'maxWidth': 'fit-content',
            'minWidth': '100px'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': '600',
            'borderBottom': '1px solid #eaecef'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        fill_width=False,
        page_current=0,
        page_action='native'
    )

def create_query_section(query_text, query_index):
    """Create a query section component"""
    if query_text is None:
        return None
    
    formatted_sql = format_sql_query(query_text)
    
    return html.Div([
        html.Div([
            html.Button([
                html.Span("Show code", id={"type": "toggle-text", "index": query_index})
            ], 
            id={"type": "toggle-query", "index": query_index}, 
            className="toggle-query-button",
            n_clicks=0)
        ], className="toggle-query-container"),
        html.Div([
            html.Pre([
                html.Code(formatted_sql, className="sql-code")
            ], className="sql-pre")
        ], 
        id={"type": "query-code", "index": query_index}, 
        className="query-code-container hidden")
    ], id={"type": "query-section", "index": query_index}, className="query-section")

def create_bot_response(content, chat_history_index):
    """Create a bot response component"""
    return html.Div([
        html.Div([
            html.Div(className="model-avatar"),
            html.Span("Genie", className="model-name")
        ], className="model-info"),
        html.Div([
            content,
            html.Div([
                html.Div([
                    html.Button([
                        html.Img(src="/assets/thumbs_up_icon.svg", alt="Thumbs up")
                    ],
                        id={"type": "thumbs-up-button", "index": chat_history_index},
                        className="thumbs-up-button"
                    ),
                    html.Button([
                        html.Img(src="/assets/thumbs_down_icon.svg", alt="Thumbs down")
                    ],
                        id={"type": "thumbs-down-button", "index": chat_history_index},
                        className="thumbs-down-button"
                    )
                ], className="message-actions")
            ], className="message-footer")
        ], className="message-content")
    ], className="bot-message message")

def create_error_response(error_msg):
    """Create an error response component"""
    return html.Div([
        html.Div([
            html.Div(className="model-avatar"),
            html.Span("Genie", className="model-name")
        ], className="model-info"),
        html.Div([
            html.Div(error_msg, className="message-text")
        ], className="message-content")
    ], className="bot-message message")