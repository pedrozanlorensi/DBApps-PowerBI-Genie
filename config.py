import os

# Default welcome text that can be customized
DEFAULT_WELCOME_TITLE = "Genie Assistant"
DEFAULT_WELCOME_DESCRIPTION = "Ask questions about your data to get granular insights!"

# Default suggestion questions
DEFAULT_SUGGESTIONS = [
    "What datasets are available?",
    "Show me recent trends in my data",
    "What are the main metrics from my business?",
    "Help me identify changes in my data over the last 30 days"
]

# Databricks configuration
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')

# Parse BI subjects with corresponding Genie spaces and Power BI URLs
def parse_bi_subjects():
    """Parse BI_SUBJECT, SPACE_ID, and POWERBI_EMBED_URL to create subject-based configuration"""
    import json
    
    def parse_env_value(env_var_name, default_value=''):
        """Parse environment variable that can be either a list or semicolon-separated string"""
        value = os.getenv(env_var_name, default_value)
        
        if not value:
            return []
        
        # If it's already a list (from YAML), return as is
        if isinstance(value, list):
            return value
        
        # Try to parse as JSON list first (in case it's passed as JSON)
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fall back to semicolon-separated string parsing for backward compatibility
        if isinstance(value, str):
            return [s.strip() for s in value.split(';') if s.strip()]
        
        return []
    
    subjects = parse_env_value('BI_SUBJECT')
    space_ids = parse_env_value('SPACE_ID')
    powerbi_urls = parse_env_value('POWERBI_EMBED_URL')
    
    # If no subjects defined, create a default configuration
    if not subjects:
        # For single values, still check the original environment variables
        single_space_id = os.getenv('SPACE_ID', '')
        single_powerbi_url = os.getenv('POWERBI_EMBED_URL', 'https://app.powerbi.com/reportEmbed?reportId=25baf2c4-2cc6-434d-94c1-157650590c23&autoAuth=true&ctid=9f37a392-f0ae-4280-9796-f1864a10effc')
        
        return [{
            'name': 'Default',
            'space_id': single_space_id,
            'powerbi_url': single_powerbi_url
        }]
    
    # Create subject configurations
    bi_subjects = []
    for i, subject in enumerate(subjects):
        space_id = space_ids[i] if i < len(space_ids) else (space_ids[0] if space_ids else '')
        powerbi_url = powerbi_urls[i] if i < len(powerbi_urls) else (powerbi_urls[0] if powerbi_urls else 'https://app.powerbi.com/reportEmbed?reportId=25baf2c4-2cc6-434d-94c1-157650590c23&autoAuth=true&ctid=9f37a392-f0ae-4280-9796-f1864a10effc')
        
        bi_subjects.append({
            'name': subject,
            'space_id': space_id,
            'powerbi_url': powerbi_url
        })
    
    return bi_subjects

# Get available BI subjects
BI_SUBJECTS = parse_bi_subjects()

# Default selections (first item in the list)
DEFAULT_SUBJECT = BI_SUBJECTS[0] if BI_SUBJECTS else {'name': 'Default', 'space_id': '', 'powerbi_url': ''}
DEFAULT_SPACE_ID = DEFAULT_SUBJECT['space_id']
DEFAULT_POWERBI_URL = DEFAULT_SUBJECT['powerbi_url']

# Legacy compatibility
POWERBI_EMBED_URL = DEFAULT_POWERBI_URL

# Legacy variables for backward compatibility
GENIE_SPACES = [{'id': subject['space_id'], 'name': subject['name']} for subject in BI_SUBJECTS]
POWERBI_DASHBOARDS = [{'url': subject['powerbi_url'], 'name': subject['name']} for subject in BI_SUBJECTS] 