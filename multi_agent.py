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



def _extract_last_assistant_text_from_output_list(output_list) -> Optional[str]:
    """Extract the last assistant message text from an 'output' event list."""
    if not isinstance(output_list, list):
        return None

    latest_text_segments = []
    # Traverse from end to start to find the last assistant message quickly
    for item in reversed(output_list):
        if isinstance(item, dict) and item.get('type') == 'message' and item.get('role') == 'assistant':
            content_list = item.get('content', [])
            if isinstance(content_list, list):
                for content_part in content_list:
                    if not isinstance(content_part, dict):
                        continue
                    text_value = content_part.get('text')
                    if isinstance(text_value, str) and text_value.strip():
                        latest_text_segments.append(text_value)
            break

    if latest_text_segments:
        # Join segments if there are multiple
        latest_text_segments.reverse()
        return "\n\n".join(latest_text_segments)
    return None


def _extract_latest_text_from_predictions(predictions) -> Optional[str]:
    """Handle predictions array that may wrap the response in various shapes."""
    if not isinstance(predictions, list) or len(predictions) == 0:
        return None

    first_prediction = predictions[0]
    if not isinstance(first_prediction, dict):
        return None

    # Case 1: predictions[0]['output'] is a list of events (same as top-level 'output')
    output_value = first_prediction.get('output')
    if isinstance(output_value, list):
        last_text = _extract_last_assistant_text_from_output_list(output_value)
        if last_text:
            return last_text

    # Case 2: predictions[0]['output'] is a dict with 'content': {'text': ...}
    if isinstance(output_value, dict):
        content_value = output_value.get('content')
        if isinstance(content_value, dict) and isinstance(content_value.get('text'), str):
            return content_value['text']

    return None


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

        # Preferred: handle top-level 'output' list of events
        if isinstance(result, dict) and isinstance(result.get('output'), list):
            latest_text = _extract_last_assistant_text_from_output_list(result['output'])
            if latest_text:
                return latest_text

        # Fallback: handle 'predictions' schema
        latest_from_predictions = _extract_latest_text_from_predictions(result.get('predictions')) if isinstance(result, dict) else None
        if latest_from_predictions:
            return latest_from_predictions
        
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
                    
                    # Chat messages (no overlay loading; we use an inline thinking indicator)
                    html.Div([], id="multi-agent-messages", className="multi-agent-messages"),
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
        ], className="multi-agent-container"),
        # Trigger store for async processing
        dcc.Store(id="multi-agent-trigger", data={"trigger": False, "message": ""}),
        html.Div(id="multi-agent-scroll-dummy")
    ], className="multi-agent-page")



def register_multi_agent_callbacks(app):
    """Register simplified multi-agent callback"""
    
    from components import create_user_message, create_bot_response, create_thinking_indicator
    
    # Step 1: append user message and a thinking indicator; trigger async call
    @app.callback(
        [Output("multi-agent-messages", "children", allow_duplicate=True),
         Output("multi-agent-input", "value", allow_duplicate=True),
         Output("multi-agent-welcome", "className", allow_duplicate=True),
         Output("multi-agent-trigger", "data", allow_duplicate=True)],
        [Input("multi-agent-send-button", "n_clicks"),
         Input("multi-agent-input", "n_submit")],
        [State("multi-agent-input", "value"),
         State("multi-agent-messages", "children")],
        prevent_initial_call=True
    )
    def handle_multi_agent_input(send_clicks, submit_clicks, input_value, current_messages):
        if not input_value or not input_value.strip():
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Add user message
        user_message = create_user_message(input_value)
        updated_messages = current_messages + [user_message] if current_messages else [user_message]
        
        # Add thinking indicator
        thinking = create_thinking_indicator()
        updated_messages.append(thinking)
        
        return (
            updated_messages,
            "",
            "multi-agent-welcome-container hidden",
            {"trigger": True, "message": input_value}
        )

    # Step 2: perform API call and replace thinking indicator with response
    @app.callback(
        [Output("multi-agent-messages", "children", allow_duplicate=True),
         Output("multi-agent-trigger", "data", allow_duplicate=True)],
        [Input("multi-agent-trigger", "data")],
        [State("multi-agent-messages", "children")],
        prevent_initial_call=True
    )
    def fetch_multi_agent_response(trigger_data, current_messages):
        if not trigger_data or not trigger_data.get("trigger"):
            return dash.no_update, dash.no_update
        
        user_input = trigger_data.get("message", "")
        if not user_input:
            return dash.no_update, {"trigger": False, "message": ""}
        
        try:
            response_text = call_multi_agent_endpoint(user_input)
            content = dcc.Markdown(response_text, className="message-text")
            bot_response = create_bot_response(content, len(current_messages))
            # Replace the last message (thinking indicator) with the bot response
            updated = (current_messages[:-1] + [bot_response]) if current_messages else [bot_response]
            return updated, {"trigger": False, "message": ""}
        except Exception as e:
            error_msg = html.Div(f"Error: {str(e)}", className="error-message")
            updated = (current_messages[:-1] + [error_msg]) if current_messages else [error_msg]
            return updated, {"trigger": False, "message": ""}


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

    # Auto-scroll to bottom when new messages render
    app.clientside_callback(
        """
        function(children) {
            var container = document.getElementById('multi-agent-messages');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
            return '';
        }
        """,
        Output('multi-agent-scroll-dummy', 'children'),
        Input('multi-agent-messages', 'children'),
        prevent_initial_call=True
    )
