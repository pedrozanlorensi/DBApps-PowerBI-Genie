from dash import html, dcc
import dash_bootstrap_components as dbc
import os
from config import (
    DEFAULT_WELCOME_TITLE, 
    DEFAULT_WELCOME_DESCRIPTION, 
    DEFAULT_SUGGESTIONS, 
    POWERBI_EMBED_URL,
    BI_SUBJECTS,
    DEFAULT_SUBJECT,
    DEFAULT_SPACE_ID,
    DEFAULT_POWERBI_URL
)
from multi_agent import create_multi_agent_page

def create_powerbi_genie_page():
    """Create the Power BI + Genie Insights page content"""
    return html.Div([
        # Left-side Chat Area (Always Visible)
        html.Div([
            html.Div([
                # Subject Selection Section (prominent placement)
                html.Div([
                    html.Div("Select Subject", className="subject-section-title"),
                    dcc.Dropdown(
                        id="subject-dropdown",
                        options=[
                            {"label": subject["name"], "value": subject["name"]} 
                            for subject in BI_SUBJECTS
                        ],
                        value=DEFAULT_SUBJECT["name"],
                        className="subject-dropdown-prominent",
                        clearable=False,
                        searchable=False
                    )
                ], className="subject-selection-section") if len(BI_SUBJECTS) > 1 else None,
                
                # Header with refresh button only
                html.Div([
                    html.Div([
                        html.Button([
                            html.Img(src="assets/sync_icon.svg", className="refresh-chat-icon")
                        ], id="new-chat-button", className="refresh-chat-button", disabled=False)
                    ], className="refresh-button-container")
                ], className="sidebar-header-minimal"),
                
                # Chat content
                html.Div([
                    # Welcome container
                    html.Div([
                        html.Div([html.Div([
                            html.Div(className="genie-logo")
                        ], className="genie-logo-container")],
                        className="genie-logo-container-header"),
                       
                                # Welcome title
                                html.Div([
                                    html.Div(id="welcome-title", className="welcome-message", children=DEFAULT_WELCOME_TITLE)
                                ], className="welcome-title-container"),
                        
                        html.Div(id="welcome-description", 
                                className="welcome-message-description",
                                children=DEFAULT_WELCOME_DESCRIPTION),
                        
                        # Suggestion buttons with IDs - using dynamic values from config
                        html.Div([
                            html.Button([
                                html.Div(className="suggestion-icon"),
                                html.Div(DEFAULT_SUGGESTIONS[0], 
                                       className="suggestion-text", id="suggestion-1-text")
                            ], id="suggestion-1", className="suggestion-button"),
                            html.Button([
                                html.Div(className="suggestion-icon"),
                                html.Div(DEFAULT_SUGGESTIONS[1],
                                       className="suggestion-text", id="suggestion-2-text")
                            ], id="suggestion-2", className="suggestion-button"),
                            html.Button([
                                html.Div(className="suggestion-icon"),
                                html.Div(DEFAULT_SUGGESTIONS[2],
                                       className="suggestion-text", id="suggestion-3-text")
                            ], id="suggestion-3", className="suggestion-button"),
                            html.Button([
                                html.Div(className="suggestion-icon"),
                                html.Div(DEFAULT_SUGGESTIONS[3],
                                       className="suggestion-text", id="suggestion-4-text")
                            ], id="suggestion-4", className="suggestion-button")
                        ], className="suggestion-buttons")
                    ], id="welcome-container", className="welcome-container visible"),
                    
                    # Chat messages
                    html.Div([], id="chat-messages", className="chat-messages"),
                ], id="chat-content", className="chat-content"),
                
                # Input area
                html.Div([
                    html.Div([
                        dcc.Input(
                            id="chat-input-fixed",
                            placeholder="Ask about your data...",
                            className="chat-input",
                            type="text",
                            disabled=False,
                            autoComplete="off"
                        ),
                        html.Div([
                            html.Button(
                                id="send-button-fixed", 
                                className="input-button send-button",
                                disabled=False
                            )
                        ], className="input-buttons-right"),
                        html.Div("You can only submit one query at a time", 
                                id="query-tooltip", 
                                className="query-tooltip hidden")
                    ], id="fixed-input-container", className="fixed-input-container"),
                    html.Div([
                        html.Div("Always review the accuracy of responses.", className="disclaimer-text"),
                        html.Div([
                            "Contact ",
                            html.A(
                                "datateam@company.com",
                                href="mailto:datateam@company.com",
                                className="email-link"
                            ),
                            " for support."
                        ], className="disclaimer-contact")
                    ], className="disclaimer-fixed"),
                ], id="fixed-input-wrapper", className="fixed-input-wrapper"),
            ], className="sidebar-content")
        ], id="sidebar", className="sidebar"),
        
        # Power BI Dashboard Area (Right Side)
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Power BI Dashboard", className="dashboard-title")
                ], className="dashboard-header"),
                html.Iframe(
                    id="powerbi-iframe",
                    src=DEFAULT_POWERBI_URL,
                    width="100%",
                    height="800",
                    className="powerbi-iframe"
                )
            ], className="dashboard-container")
        ], id="dashboard-area", className="dashboard-area"),
    ], id="main-content", className="main-content")

def create_layout():
    """Create the main application layout with Power BI embed and left-side chat"""
    return html.Div([
        # Top navigation bar
        html.Div([
            # Left component containing logos and navigation buttons
            html.Div([
                # Logos section
                html.Div([
                    html.Img(src="assets/brand_logo.png", className="brand-logo"),
                    html.Img(src="assets/databricks_logo.svg", className="databricks-logo")
                ], className="logos-container"),
                
                # Navigation buttons
                html.Div([
                    html.Button(
                        "Power BI + Genie Insights",
                        id="powerbi-genie-button",
                        className="nav-button nav-button-active"
                    ),
                    html.Button(
                        "Multi-Agent",
                        id="multi-agent-button", 
                        className="nav-button"
                    )
                ], className="nav-buttons")
            ], className="nav-left"),
            
            html.Div([
                html.Div("Y", className="user-avatar"),
                html.A(
                    html.Button(
                        "Logout",
                        id="logout-button",
                        className="logout-button"
                    ),
                    href=f"https://{os.getenv('DATABRICKS_HOST')}/login.html",
                    className="logout-link"
                )
            ], className="nav-right")
        ], className="top-nav"),
        
        # Dynamic content area that changes based on current page
        html.Div(id="page-content", children=[
            # Default: Power BI + Genie Insights page
            create_powerbi_genie_page()
        ]),
        
        html.Div(id='dummy-output'),
        dcc.Store(id="chat-trigger", data={"trigger": False, "message": ""}),
        dcc.Store(id="query-running-store", data=False),
        dcc.Store(id="selected-subject", data=DEFAULT_SUBJECT),
        dcc.Store(id="current-page", data="powerbi-genie")
    ]) 