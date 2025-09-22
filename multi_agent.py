"""
Simplified Multi-Agent functionality for the DBApps PowerBI Genie application.
"""


import requests
import os
import logging
from typing import Optional
from dash import html, dcc, Input, Output, State, callback_context
import dash
from token_minter import TokenMinter


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables
DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
CLIENT_ID = os.environ.get("DATABRICKS_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DATABRICKS_CLIENT_SECRET")
MULTI_AGENT_SERVING_ENDPOINT = os.getenv('MULTI_AGENT_SERVING_ENDPOINT')


# Initialize token minter for authentication
token_minter = TokenMinter(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    host=DATABRICKS_HOST
)



def call_multi_agent_endpoint(message: str) -> str:
    """Simple API call to multi-agent endpoint"""
    try:
        if not MULTI_AGENT_SERVING_ENDPOINT:
            return "Multi-agent endpoint not configured."
        
        payload = {
            "input": [{"role": "user", "content": message}]
        }
        
        headers = {
            "Authorization": f"Bearer {token_minter.get_token()}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            MULTI_AGENT_SERVING_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Simple response extraction
        if 'predictions' in result and len(result['predictions']) > 0:
            prediction = result['predictions'][0]
            if isinstance(prediction, dict) and 'output' in prediction:
                output = prediction['output']
                if isinstance(output, dict) and 'content' in output:
                    content = output['content']
                    if isinstance(content, dict) and 'text' in content:
                        return content['text']
        
        # Fallback: try to extract text from string representation
        result_str = str(result)
        if "'text':" in result_str:
            import re
            text_match = re.search(r"'text':\s*'([^']*)'", result_str)
            if text_match:
                return text_match.group(1)
        
        return "No response received from multi-agent system."
        
    except Exception as e:
        logger.error(f"Error calling multi-agent endpoint: {str(e)}")
        return f"Error: {str(e)}"



def create_multi_agent_page():
    """Create the simplified multi-agent page"""
    return html.Div([
        html.Div([
            html.Div([
                # Header
                html.Div([
                    html.Div("Multi-Agent Assistant", className="multi-agent-title-centered"),
                    html.Button([
                        html.Img(src="assets/sync_icon.svg", className="refresh-chat-icon")
                    ], id="multi-agent-refresh-button", className="multi-agent-refresh-button")
                ], className="multi-agent-header-top"),
                
                # Chat area
                html.Div([
                    # Welcome message
                    html.Div([
                        html.Div([
                            html.Img(src="assets/multi_agent_icon.png", className="multi-agent-logo")
                        ], className="multi-agent-logo-container"),
                        html.Div("Meet the Multi-Agent Assistant", className="multi-agent-welcome-title"),
                        html.Div("This agent interface is powered by multiple specialized AI agents that can help you answer questions about different subjects!", 
                                className="multi-agent-welcome-description"),
                        
                        # Suggestion examples for multi-agent
                        html.Div([
                            html.Div("Try asking:", className="multi-agent-suggestions-label"),
                            html.Div([
                                html.Span("• Analyze market trends", className="multi-agent-suggestion"),
                                html.Span("• Compare different strategies", className="multi-agent-suggestion"),
                                html.Span("• Generate insights from data", className="multi-agent-suggestion"),
                                html.Span("• Solve complex problems", className="multi-agent-suggestion")
                            ], className="multi-agent-suggestions-list")
                        ], className="multi-agent-suggestions")
                    ], id="multi-agent-welcome", className="multi-agent-welcome-container visible"),
                    
                    # Chat messages with loading spinner
                    dcc.Loading(
                        id="multi-agent-loading",
                        type="default",  # You can also try "graph", "cube", "circle", or "dot"
                        children=[
                            html.Div([], id="multi-agent-messages", className="multi-agent-messages")
                        ]
                    ),
                ], className="multi-agent-chat-area"),
                
                # Input area
                html.Div([
                    html.Div([
                        dcc.Input(
                            id="multi-agent-input",
                            placeholder="Ask the multi-agent system anything...",
                            className="multi-agent-input",
                            type="text",
                            autoComplete="off"
                        ),
                        html.Button([
                            html.Img(src="assets/send_icon.svg", className="send-icon")
                        ], id="multi-agent-send-button", className="multi-agent-send-button")
                    ], className="multi-agent-input-container"),
                    
                    html.Div([
                        html.Div("Always review the accuracy of responses.", className="disclaimer-text"),
                        html.Div([
                            "Contact ",
                            html.A("datateam@company.com", href="mailto:datateam@company.com", className="email-link"),
                            " for support."
                        ], className="disclaimer-contact"),
                    ], className="multi-agent-disclaimer-centered"),
                ], className="multi-agent-input-wrapper")
            ], className="multi-agent-content")
        ], className="multi-agent-container")
    ], className="multi-agent-page")



def register_multi_agent_callbacks(app):
    """Register simplified multi-agent callback"""
    
    from components import create_user_message, create_bot_response
    
    @app.callback(
        [Output("multi-agent-messages", "children"),
         Output("multi-agent-input", "value"),
         Output("multi-agent-welcome", "className")],
        [Input("multi-agent-send-button", "n_clicks"),
         Input("multi-agent-input", "n_submit")],
        [State("multi-agent-input", "value"),
         State("multi-agent-messages", "children")],
        prevent_initial_call=True
    )
    def handle_multi_agent_input(send_clicks, submit_clicks, input_value, current_messages):
        if not input_value or not input_value.strip():
            return dash.no_update, dash.no_update, dash.no_update
        
        # Add user message
        user_message = create_user_message(input_value)
        updated_messages = current_messages + [user_message] if current_messages else [user_message]
        
        # Call API and get response
        try:
            response_text = call_multi_agent_endpoint(input_value)
            
            # Create bot response
            content = dcc.Markdown(response_text, className="message-text")
            bot_response = create_bot_response(content, len(updated_messages))
            updated_messages.append(bot_response)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            error_response = html.Div(error_msg, className="error-message")
            updated_messages.append(error_response)
        
        return updated_messages, "", "multi-agent-welcome-container hidden"


    @app.callback(
        [Output("multi-agent-messages", "children", allow_duplicate=True),
         Output("multi-agent-welcome", "className", allow_duplicate=True)],
        [Input("multi-agent-refresh-button", "n_clicks")],
        prevent_initial_call=True
    )
    def refresh_multi_agent_chat(n_clicks):
        if n_clicks:
            return [], "multi-agent-welcome-container visible"
        return dash.no_update, dash.no_update
