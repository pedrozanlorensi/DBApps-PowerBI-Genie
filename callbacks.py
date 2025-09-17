from dash import Input, Output, State, callback, ALL, MATCH, callback_context, no_update, clientside_callback, html, dcc
import dash
import json
import pandas as pd
from genie_room import genie_query
from components import (
    create_user_message, 
    create_thinking_indicator, 
    create_data_table, 
    create_query_section, 
    create_bot_response, 
    create_error_response
)
from config import DEFAULT_WELCOME_TITLE, DEFAULT_WELCOME_DESCRIPTION, DEFAULT_SUGGESTIONS

def register_callbacks(app):
    """Register all callbacks with the Dash app"""
    
    # Import and register multi-agent callbacks
    from multi_agent import register_multi_agent_callbacks
    register_multi_agent_callbacks(app)
    
    # First callback: Handle inputs and show thinking indicator
    @app.callback(
        [Output("chat-messages", "children", allow_duplicate=True),
         Output("chat-input-fixed", "value", allow_duplicate=True),
         Output("welcome-container", "className", allow_duplicate=True),
         Output("chat-trigger", "data", allow_duplicate=True),
         Output("query-running-store", "data", allow_duplicate=True)],
        [Input("suggestion-1", "n_clicks"),
         Input("suggestion-2", "n_clicks"),
         Input("suggestion-3", "n_clicks"),
         Input("suggestion-4", "n_clicks"),
         Input("send-button-fixed", "n_clicks"),
         Input("chat-input-fixed", "n_submit")],
        [State("suggestion-1-text", "children"),
         State("suggestion-2-text", "children"),
         State("suggestion-3-text", "children"),
         State("suggestion-4-text", "children"),
         State("chat-input-fixed", "value"),
         State("chat-messages", "children"),
         State("welcome-container", "className")],
        prevent_initial_call=True
    )
    def handle_all_inputs(s1_clicks, s2_clicks, s3_clicks, s4_clicks, send_clicks, submit_clicks,
                         s1_text, s2_text, s3_text, s4_text, input_value, current_messages,
                         welcome_class):
        ctx = callback_context
        if not ctx.triggered:
            return [no_update] * 8

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Handle suggestion buttons
        suggestion_map = {
            "suggestion-1": s1_text,
            "suggestion-2": s2_text,
            "suggestion-3": s3_text,
            "suggestion-4": s4_text
        }
        
        # Get the user input based on what triggered the callback
        if trigger_id in suggestion_map:
            user_input = suggestion_map[trigger_id]
        else:
            user_input = input_value
        
        if not user_input:
            return [no_update] * 5
        
        # Create user message
        user_message = create_user_message(user_input)
        
        # Add the user message to the chat
        updated_messages = current_messages + [user_message] if current_messages else [user_message]
        
        # Add thinking indicator
        thinking_indicator = create_thinking_indicator()
        updated_messages.append(thinking_indicator)
        
        return (updated_messages, "", "welcome-container hidden",
                {"trigger": True, "message": user_input}, True)

    # Second callback: Make API call and show response
    @app.callback(
        [Output("chat-messages", "children", allow_duplicate=True),
         Output("chat-trigger", "data", allow_duplicate=True),
         Output("query-running-store", "data", allow_duplicate=True)],
        [Input("chat-trigger", "data")],
        [State("chat-messages", "children"),
         State("selected-subject", "data")],
        prevent_initial_call=True
    )
    def get_model_response(trigger_data, current_messages, selected_subject):
        if not trigger_data or not trigger_data.get("trigger"):
            return dash.no_update, dash.no_update, dash.no_update
        
        user_input = trigger_data.get("message", "")
        if not user_input:
            return dash.no_update, dash.no_update, dash.no_update
        
        try:
            # Extract the space ID from the selected subject
            selected_space_id = selected_subject.get('space_id') if selected_subject else None
            response, query_text = genie_query(user_input, selected_space_id)
            
            if isinstance(response, str):
                content = dcc.Markdown(response, className="message-text")
            else:
                # Data table response
                df = pd.DataFrame(response)
                
                # Create the table
                table_id = f"table-{len(current_messages)}"
                data_table = create_data_table(df, table_id)

                # Format SQL query if available
                query_section = None
                if query_text is not None:
                    query_index = f"{len(current_messages)}-{len(current_messages)}"
                    query_section = create_query_section(query_text, query_index)

                # Create content with table and optional SQL section
                content = html.Div([
                    html.Div([data_table], style={
                        'marginBottom': '20px',
                        'paddingRight': '5px'
                    }),
                    query_section if query_section else None,
                ])
            
            # Create bot response
            bot_response = create_bot_response(content, 0)
            
            return current_messages[:-1] + [bot_response], {"trigger": False, "message": ""}, False
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}. Please try again later."
            error_response = create_error_response(error_msg)
            
            return current_messages[:-1] + [error_response], {"trigger": False, "message": ""}, False





    # Modify the new chat button callback to reset session
    @app.callback(
        [Output("welcome-container", "className", allow_duplicate=True),
         Output("chat-messages", "children", allow_duplicate=True),
         Output("chat-trigger", "data", allow_duplicate=True),
         Output("query-running-store", "data", allow_duplicate=True)],
        [Input("new-chat-button", "n_clicks")],
        [State("chat-messages", "children"),
         State("chat-trigger", "data"),
         State("query-running-store", "data")],
        prevent_initial_call=True
    )
    def reset_to_welcome(n_clicks, chat_messages, chat_trigger, query_running):
        # Reset session when starting a new chat
        return ("welcome-container visible", [], {"trigger": False, "message": ""}, False)

    @app.callback(
        [Output("welcome-container", "className", allow_duplicate=True)],
        [Input("chat-messages", "children")],
        prevent_initial_call=True
    )
    def reset_query_running(chat_messages):
        # Return as a single-item list
        if chat_messages:
            return ["welcome-container hidden"]
        else:
            return ["welcome-container visible"]

    # Add callback to disable input while query is running
    @app.callback(
        [Output("chat-input-fixed", "disabled"),
         Output("send-button-fixed", "disabled"),
         Output("new-chat-button", "disabled"),
         Output("query-tooltip", "className")],
        [Input("query-running-store", "data")],
        prevent_initial_call=True
    )
    def toggle_input_disabled(query_running):
        # Show tooltip when query is running, hide it otherwise
        tooltip_class = "query-tooltip visible" if query_running else "query-tooltip hidden"
        
        # Disable input and buttons when query is running
        return query_running, query_running, query_running, tooltip_class

    # Fix the callback for thumbs up/down buttons
    @app.callback(
        [Output({"type": "thumbs-up-button", "index": MATCH}, "className"),
         Output({"type": "thumbs-down-button", "index": MATCH}, "className")],
        [Input({"type": "thumbs-up-button", "index": MATCH}, "n_clicks"),
         Input({"type": "thumbs-down-button", "index": MATCH}, "n_clicks")],
        [State({"type": "thumbs-up-button", "index": MATCH}, "className"),
         State({"type": "thumbs-down-button", "index": MATCH}, "className")],
        prevent_initial_call=True
    )
    def handle_feedback(up_clicks, down_clicks, up_class, down_class):
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        button_type = json.loads(trigger_id)["type"]
        
        if button_type == "thumbs-up-button":
            new_up_class = "thumbs-up-button active" if "active" not in up_class else "thumbs-up-button"
            new_down_class = "thumbs-down-button"
        else:
            new_up_class = "thumbs-up-button"
            new_down_class = "thumbs-down-button active" if "active" not in down_class else "thumbs-down-button"
        
        return new_up_class, new_down_class

    # Add callback for toggling SQL query visibility
    @app.callback(
        [Output({"type": "query-code", "index": MATCH}, "className"),
         Output({"type": "toggle-text", "index": MATCH}, "children")],
        [Input({"type": "toggle-query", "index": MATCH}, "n_clicks")],
        prevent_initial_call=True
    )
    def toggle_query_visibility(n_clicks):
        if n_clicks % 2 == 1:
            return "query-code-container visible", "Hide code"
        return "query-code-container hidden", "Show code"


    # Callback for updating selected subject, Power BI iframe, and clearing chat when dropdown changes
    @app.callback(
        [Output("selected-subject", "data"),
         Output("powerbi-iframe", "src"),
         Output("chat-messages", "children", allow_duplicate=True),
         Output("welcome-container", "className", allow_duplicate=True),
         Output("chat-trigger", "data", allow_duplicate=True),
         Output("query-running-store", "data", allow_duplicate=True)],
        [Input("subject-dropdown", "value")],
        prevent_initial_call=True
    )
    def update_selected_subject(selected_subject_name):
        from config import BI_SUBJECTS
        
        # Find the selected subject
        selected_subject = None
        for subject in BI_SUBJECTS:
            if subject['name'] == selected_subject_name:
                selected_subject = subject
                break
        
        if selected_subject:
            # Clear chat and show welcome screen when subject changes
            return [
                selected_subject, 
                selected_subject['powerbi_url'],
                [],  # Clear chat messages
                "welcome-container visible",  # Show welcome screen
                {"trigger": False, "message": ""},  # Reset chat trigger
                False  # Reset query running state
            ]
        else:
            # Fallback to first subject if not found
            default_subject = BI_SUBJECTS[0] if BI_SUBJECTS else {'name': 'Default', 'space_id': '', 'powerbi_url': ''}
            return [
                default_subject, 
                default_subject['powerbi_url'],
                [],  # Clear chat messages
                "welcome-container visible",  # Show welcome screen
                {"trigger": False, "message": ""},  # Reset chat trigger
                False  # Reset query running state
            ]

    # Navigation callbacks for switching between pages
    @app.callback(
        [Output("page-content", "children"),
         Output("powerbi-genie-button", "className"),
         Output("multi-agent-button", "className"),
         Output("current-page", "data")],
        [Input("powerbi-genie-button", "n_clicks"),
         Input("multi-agent-button", "n_clicks")],
        prevent_initial_call=True
    )
    def handle_navigation(powerbi_clicks, multi_agent_clicks):
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "powerbi-genie-button":
            # Refresh Power BI + Genie page by reloading modules and creating fresh page
            import importlib
            import sys
            
            # Reload layout module to ensure fresh state
            if 'layout' in sys.modules:
                importlib.reload(sys.modules['layout'])
            if 'config' in sys.modules:
                importlib.reload(sys.modules['config'])
            
            from layout import create_powerbi_genie_page
            
            return [
                create_powerbi_genie_page(),
                "nav-button nav-button-active",
                "nav-button", 
                "powerbi-genie"
            ]
        elif button_id == "multi-agent-button":
            # Refresh Multi-Agent page by reloading modules and creating fresh page
            import importlib
            import sys
            
            # Reload multi_agent module to ensure fresh state
            if 'multi_agent' in sys.modules:
                importlib.reload(sys.modules['multi_agent'])
            
            from multi_agent import create_multi_agent_page
            
            return [
                create_multi_agent_page(),
                "nav-button",
                "nav-button nav-button-active",
                "multi-agent"
            ]
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


    # Modify the clientside callback to target the chat-container
    app.clientside_callback(
        """
        function(children) {
            var chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            return '';
        }
        """,
        Output('dummy-output', 'children'),
        Input('chat-messages', 'children'),
        prevent_initial_call=True
    ) 