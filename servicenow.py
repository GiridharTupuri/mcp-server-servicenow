import os
import httpx
import json
from datetime import timedelta
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# --- Configuration ---
load_dotenv()  # Load variables from .env file

SN_INSTANCE = os.getenv("SERVICENOW_INSTANCE")
SN_USERNAME = os.getenv("SERVICENOW_USERNAME")
SN_PASSWORD = os.getenv("SERVICENOW_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Loaded, but not used in these tools yet

# Basic input validation
if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    raise ValueError(
        "ServiceNow instance, username, and password must be set in .env file"
    )

# --- Initialize FastMCP Server ---
# Give the server a name that will appear in the client UI
mcp = FastMCP()


# --- ServiceNow API Helper ---
async def _make_servicenow_request(
    endpoint: str, payload: dict, method: str = "POST"
) -> dict:
    """Helper function to make authenticated requests to the ServiceNow Table API."""
    api_url = f"{SN_INSTANCE.rstrip('/')}/{endpoint}"
    auth = (SN_USERNAME, SN_PASSWORD)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(auth=auth, headers=headers, timeout=30.0) as client:
        try:
            print(
                f"Making {method} request to {api_url} with payload: {json.dumps(payload)}"
            )  # Debug print
            if method == "POST":
                response = await client.post(api_url, json=payload)
            elif method == "GET":
                response = await client.get(api_url, params=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raise exception for 4xx/5xx errors
            print(
                f"ServiceNow API Response Status: {response.status_code}"
            )  # Debug print
            # Handle potential empty responses for certain successful actions
            if response.status_code == 204:  # No Content
                return {
                    "status": "success",
                    "message": "Operation successful (No Content)",
                }
            if response.status_code == 201:  # Created
                # Standard response for table API creation usually has 'result'
                return response.json().get(
                    "result", {"status": "success", "message": "Record created"}
                )
            # Handle other successful status codes if necessary
            return response.json().get(
                "result", {}
            )  # Return the 'result' part or empty dict

        except httpx.HTTPStatusError as e:
            error_details = f"HTTP Error: {e.response.status_code} - {e.response.text}"
            print(error_details)  # Log the error
            # Attempt to parse ServiceNow specific error message if available
            try:
                sn_error = e.response.json().get("error", {})
                message = sn_error.get("message", "Unknown ServiceNow Error")
                detail = sn_error.get("detail", e.response.text)
                raise ValueError(f"ServiceNow API Error: {message} - {detail}") from e
            except json.JSONDecodeError:
                # If response is not JSON
                raise ValueError(error_details) from e
            except Exception as inner_e:
                # Catch potential issues parsing the error itself
                print(f"Error parsing ServiceNow error response: {inner_e}")
                raise ValueError(
                    error_details
                ) from e  # Raise the original HTTP error details
        except httpx.RequestError as e:
            error_details = f"Request Error: {e}"
            print(error_details)
            raise ValueError(f"Could not connect to ServiceNow: {error_details}") from e
        except Exception as e:
            # Catch-all for other unexpected errors during the request
            error_details = (
                f"Unexpected error during ServiceNow request: {type(e).__name__} - {e}"
            )
            print(error_details)
            raise ValueError(error_details) from e


# --- ServiceNow GET Helper ---
async def sn_get(table: str, limit: int = 5) -> dict:
    """Helper function to retrieve records from ServiceNow tables."""
    endpoint = f"api/now/table/{table}"
    params = {
        "sysparm_limit": limit,
        "sysparm_display_value": "true"
    }
    return await _make_servicenow_request(endpoint, params, method="GET")


# --- MCP Tool Definitions ---


@mcp.tool()
async def create_incident(
    short_description: str,
    description: str | None = None,
    caller_id: str | None = None,  # Optional: User sys_id or name
    urgency: str | None = "3",  # Default to Low
    impact: str | None = "3",  # Default to Low
) -> str:
    """Creates a new incident record in ServiceNow.
    Args:
        short_description: A brief summary of the incident.
        description: A detailed description of the incident (optional).
        caller_id: The user reporting the incident (name or sys_id, optional).
        urgency: Urgency level (1-High, 2-Medium, 3-Low, optional, default Low).
        impact: Impact level (1-High, 2-Medium, 3-Low, optional, default Low).
    Returns:
        A confirmation message with the new incident number.
    """
    endpoint = "api/now/table/incident"
    payload = {
        "short_description": short_description,
        "description": description
        or short_description,  # Use short desc if long not provided
        "urgency": urgency,
        "impact": impact,
    }
    if caller_id:
        payload["caller_id"] = caller_id  # SN resolves name to sys_id often

    try:
        result = await _make_servicenow_request(endpoint, payload)
        incident_number = result.get("number", "UNKNOWN")
        sys_id = result.get("sys_id", "UNKNOWN")
        return f"Successfully created incident {incident_number} (Sys ID: {sys_id})."
    except ValueError as e:
        # Catch errors from the helper and return them as string results for the LLM
        return f"Error creating incident: {e}"


@mcp.tool()
async def create_kb_article(
    short_description: str,
    article_body: str,
    kb_knowledge_base: (
        str | None
    ) = None,  # Optional: sys_id or name of the knowledge base
    workflow_state: (
        str | None
    ) = "draft",  # Optional: e.g., 'draft', 'review', 'published'
) -> str:
    """Creates a new knowledge base article in ServiceNow.
    Args:
        short_description: The title or brief summary of the article.
        article_body: The main content of the knowledge article (HTML or plain text).
        kb_knowledge_base: The sys_id or name of the Knowledge Base to add the article to (optional).
        workflow_state: The initial state of the article (optional, default 'draft').
    Returns:
        A confirmation message with the new KB article number.
    """
    endpoint = "api/now/table/kb_knowledge"
    payload = {
        "short_description": short_description,
        "text": article_body,  # Use 'text' field for kb_knowledge body often
        "workflow_state": workflow_state,
        "article_type": "text",  # Assuming a standard text article
    }
    if kb_knowledge_base:
        payload["kb_knowledge_base"] = kb_knowledge_base

    try:
        result = await _make_servicenow_request(endpoint, payload)
        kb_number = result.get("number", "UNKNOWN")
        sys_id = result.get("sys_id", "UNKNOWN")
        return f"Successfully created KB article {kb_number} (Sys ID: {sys_id})."
    except ValueError as e:
        return f"Error creating KB article: {e}"


@mcp.tool()
async def create_client_script(
    name: str,
    table: str,  # sys_db_object name, e.g., 'incident'
    script: str,
    ui_type: str = "all",  # 'all', 'desktop', 'mobile', 'service_portal'
    script_type: str = "onChange",  # e.g., 'onLoad', 'onChange', 'onSubmit', 'onCellEdit'
    field_name: str | None = None,  # Required for onChange type
    is_active: bool = True,
) -> str:
    """Creates a new Client Script in ServiceNow.
    Args:
        name: The name of the client script.
        table: The table name the script applies to (e.g., 'incident').
        script: The JavaScript code for the client script.
        ui_type: Where the script runs ('all', 'desktop', 'mobile', 'service_portal', default 'all').
        script_type: When the script runs ('onLoad', 'onChange', 'onSubmit', 'onCellEdit', default 'onChange').
        field_name: The field name that triggers the script (required for 'onChange').
        is_active: Whether the script should be active (default True).
    Returns:
        A confirmation message with the name of the created client script.
    """
    if script_type == "onChange" and not field_name:
        return "Error: 'field_name' is required when script_type is 'onChange'."

    endpoint = "api/now/table/sys_script_client"
    payload = {
        "name": name,
        "table": table,
        "script": script,
        "ui_type": ui_type,
        "type": script_type,
        "active": str(
            is_active
        ).lower(),  # ServiceNow often expects strings for booleans
    }
    if field_name:
        payload["field_name"] = field_name

    try:
        result = await _make_servicenow_request(endpoint, payload)
        script_name = result.get("name", name)  # API might not return name predictably
        sys_id = result.get("sys_id", "UNKNOWN")
        return f"Successfully created Client Script '{script_name}' (Sys ID: {sys_id})."
    except ValueError as e:
        return f"Error creating Client Script: {e}"


@mcp.tool()
async def create_business_rule(
    name: str,
    table: str,  # sys_db_object name, e.g., 'incident'
    script: str,
    when: str = "before",  # 'before', 'after', 'async', 'display'
    order: int = 100,
    action_insert: bool = True,
    action_update: bool = True,
    action_delete: bool = False,
    action_query: bool = False,
    is_active: bool = True,
) -> str:
    """Creates a new Business Rule in ServiceNow.
    Args:
        name: The name of the business rule.
        table: The table name the rule applies to (e.g., 'incident').
        script: The server-side JavaScript code for the rule.
        when: When the rule runs ('before', 'after', 'async', 'display', default 'before').
        order: Execution order (lower runs first, default 100).
        action_insert: Run on insert (default True).
        action_update: Run on update (default True).
        action_delete: Run on delete (default False).
        action_query: Run on query (default False).
        is_active: Whether the rule should be active (default True).
    Returns:
        A confirmation message with the name of the created business rule.
    """
    endpoint = "api/now/table/sys_script"  # Business Rules are in sys_script table
    payload = {
        "name": name,
        "table": table,
        "script": script,
        "when": when,
        "order": order,
        "action_insert": str(action_insert).lower(),
        "action_update": str(action_update).lower(),
        "action_delete": str(action_delete).lower(),
        "action_query": str(action_query).lower(),
        "active": str(is_active).lower(),
        "collection": table,  # Often needed redundancy
    }

    try:
        result = await _make_servicenow_request(endpoint, payload)
        rule_name = result.get("name", name)
        sys_id = result.get("sys_id", "UNKNOWN")
        return f"Successfully created Business Rule '{rule_name}' (Sys ID: {sys_id})."
    except ValueError as e:
        return f"Error creating Business Rule: {e}"


@mcp.tool()
async def create_sla_definition(
    name: str,
    table: str,  # e.g., 'incident'
    duration_seconds: int,  # Duration in seconds
    start_condition: str | None = None,  # Encoded query condition when SLA starts
    stop_condition: str | None = None,  # Encoded query condition when SLA stops
    pause_condition: str | None = None,  # Encoded query condition when SLA pauses
) -> str:
    """Creates a basic SLA Definition in ServiceNow. Note: Conditions require encoded queries.
    Args:
        name: The name of the SLA Definition.
        table: The table name the SLA applies to (e.g., 'incident').
        duration_seconds: The target duration of the SLA in seconds.
        start_condition: Encoded query for when the SLA attaches (optional).
        stop_condition: Encoded query for when the SLA completes (optional).
        pause_condition: Encoded query for when the SLA pauses (optional).
    Returns:
        A confirmation message with the name of the created SLA Definition.
    """
    endpoint = "api/now/table/contract_sla"
    # Duration needs specific GlideDuration format '1970-01-01 HH:MM:SS' relative to epoch start
    # Example: 8 hours = 28800 seconds -> 1970-01-01 08:00:00
    td = timedelta(seconds=duration_seconds)
    glide_duration = (
        f"1970-01-01 {str(td).split('.')[0].zfill(8)}"  # Format as HH:MM:SS
    )

    payload = {
        "name": name,
        "target_table": table,
        "duration": glide_duration,
        "duration_type": "glide_duration",  # Specify duration type
        "type": "SLA",  # Standard SLA type
        "active": "true",
    }
    if start_condition:
        payload["start_condition"] = start_condition
    if stop_condition:
        payload["stop_condition"] = stop_condition
    if pause_condition:
        payload["pause_condition"] = pause_condition

    try:
        result = await _make_servicenow_request(endpoint, payload)
        sla_name = result.get("name", name)
        sys_id = result.get("sys_id", "UNKNOWN")
        return f"Successfully created SLA Definition '{sla_name}' (Sys ID: {sys_id}). Conditions should be verified in ServiceNow UI."
    except ValueError as e:
        return f"Error creating SLA Definition: {e}"


# @mcp.tool()
# async def create_record_producer(
#     name: str,
#     table_name: str,  # The target table for the record produced
#     short_description: str | None = None,
#     category_sys_id: (
#         str | None
#     ) = None,  # Optional: sys_id of the Service Catalog category
#     script: str | None = None,  # Optional: Server-side script for the producer
# ) -> str:
#     """Creates a new Record Producer in ServiceNow's Service Catalog.
#     Args:
#         name: The name of the Record Producer (how it appears in the catalog).
#         table_name: The name of the table where the record will be created (e.g., 'incident').
#         short_description: A short description displayed in the catalog (optional).
#         category_sys_id: The sys_id of the Service Catalog Category (optional).
#         script: Server-side script to run when the producer is submitted (optional).
#     Returns:
#         A confirmation message with the name of the created Record Producer.
#     """
#     endpoint = "api/now/table/sc_cat_item_producer"
#     payload = {
#         "name": name,
#         "table_name": table_name,
#         "short_description": short_description or name,
#         "active": "true",
#         "sys_class_name": "sc_cat_item_producer",  # Important for record producers
#     }
#     if category_sys_id:
#         payload["category"] = category_sys_id
#     if script:
#         payload["script"] = script

#     try:
#         result = await _make_servicenow_request(endpoint, payload)
#         producer_name = result.get("name", name)
#         sys_id = result.get("sys_id", "UNKNOWN")
#         return f"Successfully created Record Producer '{producer_name}' (Sys ID: {sys_id}). Variables need to be added via ServiceNow UI."
#     except ValueError as e:
#         return f"Error creating Record Producer: {e}"

@mcp.tool()
async def create_record_producer(
    name: str,
    table_name: str,  # The target table for the record produced
    short_description: str | None = None,
    category_sys_id: str | None = None,  # Optional: sys_id of the Service Catalog category
    script: str | None = None,  # Optional: Server-side script for the producer
    variables: list[dict] | None = None,  # Optional: List of variable definitions
    variable_set_ids: list[str] | None = None,  # Optional: List of variable set sys_ids to include
) -> str:
    """Creates a new Record Producer in ServiceNow's Service Catalog with support for variables.
    
    Args:
        name: The name of the Record Producer (how it appears in the catalog).
        table_name: The name of the table where the record will be created (e.g., 'incident').
        short_description: A short description displayed in the catalog (optional).
        category_sys_id: The sys_id of the Service Catalog Category (optional).
        script: Server-side script to run when the producer is submitted (optional).
        variables: List of dictionaries defining variables to add to the Record Producer (optional).
                  Each dictionary should contain variable details such as:
                  {
                      "name": "variable_name",
                      "label": "User-friendly Label",
                      "type": "string|boolean|integer|etc",
                      "mandatory": True/False,
                      "default_value": "optional default",
                      "reference_table": "table_name",  # For reference variables
                      "help_text": "Tooltip text",
                      "description": "Longer description"
                  }
        variable_set_ids: List of sys_ids of variable sets to include (optional).
        
    Returns:
        A confirmation message with the name of the created Record Producer and added variables.
    """
    # First create the Record Producer
    endpoint = "api/now/table/sc_cat_item_producer"
    payload = {
        "name": name,
        "table_name": table_name,
        "short_description": short_description or name,
        "active": "true",
        "sys_class_name": "sc_cat_item_producer",  # Important for record producers
    }
    if category_sys_id:
        payload["category"] = category_sys_id
    if script:
        payload["script"] = script

    try:
        # Create the Record Producer first
        result = await _make_servicenow_request(endpoint, payload)
        producer_name = result.get("name", name)
        producer_sys_id = result.get("sys_id", "")
        
        if not producer_sys_id:
            return "Error creating Record Producer: No sys_id returned from ServiceNow."
        
        # Add variable sets if provided
        variable_set_messages = []
        if variable_set_ids and len(variable_set_ids) > 0:
            for set_id in variable_set_ids:
                try:
                    # Create catalog item variable set relationship
                    set_endpoint = "api/now/table/io_set_item"
                    set_payload = {
                        "sc_cat_item": producer_sys_id,
                        "variable_set": set_id,
                    }
                    
                    set_result = await _make_servicenow_request(set_endpoint, set_payload)
                    if set_result.get("sys_id"):
                        variable_set_messages.append(f"Added variable set (ID: {set_id})")
                    else:
                        variable_set_messages.append(f"Failed to add variable set (ID: {set_id})")
                except ValueError as e:
                    variable_set_messages.append(f"Error adding variable set (ID: {set_id}): {e}")
        
        # Add individual variables if provided
        variable_messages = []
        if variables and len(variables) > 0:
            for idx, var_def in enumerate(variables):
                try:
                    # Map variable type to ServiceNow's internal variable type
                    var_type_map = {
                        "string": "2",
                        "integer": "9",
                        "boolean": "6",
                        "reference": "8",
                        "choice": "3",
                        "text": "1",
                        "date": "5",
                        "datetime": "4",
                        "currency": "10",
                        "price": "7"
                    }
                    
                    # Create catalog item variable
                    var_endpoint = "api/now/table/item_option_new"
                    var_payload = {
                        "cat_item": producer_sys_id,
                        "name": var_def.get("name", f"variable_{idx}"),
                        "question_text": var_def.get("label", var_def.get("name", f"Variable {idx}")),
                        "type": var_type_map.get(var_def.get("type", "string").lower(), "2"),  # Default to string
                        "mandatory": str(var_def.get("mandatory", False)).lower(),
                        "order": (idx + 1) * 100,  # Incrementing order for proper display
                        "help_text": var_def.get("help_text", ""),
                        "description": var_def.get("description", ""),
                    }
                    
                    # Add default value if provided
                    if "default_value" in var_def:
                        var_payload["default_value"] = str(var_def["default_value"])
                    
                    # Add reference table for reference variables
                    if var_def.get("type", "").lower() == "reference" and "reference_table" in var_def:
                        var_payload["reference"] = var_def["reference_table"]
                    
                    var_result = await _make_servicenow_request(var_endpoint, var_payload)
                    if var_result.get("sys_id"):
                        variable_messages.append(f"Added variable '{var_def.get('name', f'variable_{idx}')}'")
                    else:
                        variable_messages.append(f"Failed to add variable '{var_def.get('name', f'variable_{idx}')}'")
                except ValueError as e:
                    variable_messages.append(f"Error adding variable '{var_def.get('name', f'variable_{idx}')}': {e}")
        
        # Construct final result message
        message = f"Successfully created Record Producer '{producer_name}' (Sys ID: {producer_sys_id})."
        
        if variable_set_messages:
            message += f"\nVariable Sets: {'; '.join(variable_set_messages)}"
            
        if variable_messages:
            message += f"\nVariables: {'; '.join(variable_messages)}"
        elif not variable_set_messages and not variables:
            message += " No variables were added."
            
        return message
    except ValueError as e:
        return f"Error creating Record Producer: {e}"


@mcp.tool()
async def create_variable_set(
    name: str,
    description: str | None = None,
    variables: list[dict] | None = None,  # Optional: List of variable definitions
) -> str:
    """Creates a new Variable Set in ServiceNow to be reused across catalog items.
    
    Args:
        name: The name of the Variable Set.
        description: A description of the Variable Set (optional).
        variables: List of dictionaries defining variables to add to the set (optional).
                  Each dictionary should contain variable details such as:
                  {
                      "name": "variable_name",
                      "label": "User-friendly Label",
                      "type": "string|boolean|integer|etc",
                      "mandatory": True/False,
                      "default_value": "optional default",
                      "reference_table": "table_name",  # For reference variables
                      "help_text": "Tooltip text", 
                      "description": "Longer description"
                  }
        
    Returns:
        A confirmation message with the sys_id of the created Variable Set.
    """
    # First create the Variable Set
    endpoint = "api/now/table/io_set"
    payload = {
        "name": name,
        "description": description or name,
        "active": "true",
    }

    try:
        # Create the Variable Set first
        result = await _make_servicenow_request(endpoint, payload)
        set_name = result.get("name", name)
        set_sys_id = result.get("sys_id", "")
        
        if not set_sys_id:
            return "Error creating Variable Set: No sys_id returned from ServiceNow."
        
        # Add variables if provided
        variable_messages = []
        if variables and len(variables) > 0:
            for idx, var_def in enumerate(variables):
                try:
                    # Map variable type to ServiceNow's internal variable type
                    var_type_map = {
                        "string": "2",
                        "integer": "9",
                        "boolean": "6",
                        "reference": "8",
                        "choice": "3",
                        "text": "1",
                        "date": "5",
                        "datetime": "4",
                        "currency": "10",
                        "price": "7"
                    }
                    
                    # Create variable in the set
                    var_endpoint = "api/now/table/io_set_variable"
                    var_payload = {
                        "variable_set": set_sys_id,
                        "name": var_def.get("name", f"variable_{idx}"),
                        "question_text": var_def.get("label", var_def.get("name", f"Variable {idx}")),
                        "type": var_type_map.get(var_def.get("type", "string").lower(), "2"),  # Default to string
                        "mandatory": str(var_def.get("mandatory", False)).lower(),
                        "order": (idx + 1) * 100,  # Incrementing order for proper display
                        "help_text": var_def.get("help_text", ""),
                        "description": var_def.get("description", ""),
                    }
                    
                    # Add default value if provided
                    if "default_value" in var_def:
                        var_payload["default_value"] = str(var_def["default_value"])
                    
                    # Add reference table for reference variables
                    if var_def.get("type", "").lower() == "reference" and "reference_table" in var_def:
                        var_payload["reference"] = var_def["reference_table"]
                    
                    var_result = await _make_servicenow_request(var_endpoint, var_payload)
                    if var_result.get("sys_id"):
                        variable_messages.append(f"Added variable '{var_def.get('name', f'variable_{idx}')}'")
                    else:
                        variable_messages.append(f"Failed to add variable '{var_def.get('name', f'variable_{idx}')}'")
                except ValueError as e:
                    variable_messages.append(f"Error adding variable '{var_def.get('name', f'variable_{idx}')}': {e}")
        
        # Construct final result message
        message = f"Successfully created Variable Set '{set_name}' (Sys ID: {set_sys_id})."
        
        if variable_messages:
            message += f"\nVariables: {'; '.join(variable_messages)}"
        else:
            message += " No variables were added."
            
        return message
    except ValueError as e:
        return f"Error creating Variable Set: {e}"


@mcp.tool()
async def get_incidents(limit: int = 5) -> str:
    """Retrieve recent incidents from ServiceNow.
    Args:
        limit: Number of incidents to retrieve (default 5, max 100).
    Returns:
        A formatted string with incident details.
    """
    try:
        if limit > 100:
            limit = 100
        result = await sn_get("incident", limit=limit)
        
        if not result or "result" not in result:
            return "No incidents found or error retrieving incidents."
        
        incidents = result["result"]
        if not incidents:
            return "No incidents found."
        
        formatted_incidents = []
        for incident in incidents:
            formatted_incidents.append(
                f"• {incident.get('number', 'N/A')}: {incident.get('short_description', 'No description')} "
                f"(State: {incident.get('state', 'N/A')}, Priority: {incident.get('priority', 'N/A')})"
            )
        
        return f"Retrieved {len(incidents)} incidents:\n" + "\n".join(formatted_incidents)
    except ValueError as e:
        return f"Error retrieving incidents: {e}"


@mcp.tool()
async def get_change_requests(limit: int = 5) -> str:
    """Retrieve recent change requests from ServiceNow.
    Args:
        limit: Number of change requests to retrieve (default 5, max 100).
    Returns:
        A formatted string with change request details.
    """
    try:
        if limit > 100:
            limit = 100
        result = await sn_get("change_request", limit=limit)
        
        if not result or "result" not in result:
            return "No change requests found or error retrieving change requests."
        
        changes = result["result"]
        if not changes:
            return "No change requests found."
        
        formatted_changes = []
        for change in changes:
            formatted_changes.append(
                f"• {change.get('number', 'N/A')}: {change.get('short_description', 'No description')} "
                f"(State: {change.get('state', 'N/A')}, Risk: {change.get('risk', 'N/A')})"
            )
        
        return f"Retrieved {len(changes)} change requests:\n" + "\n".join(formatted_changes)
    except ValueError as e:
        return f"Error retrieving change requests: {e}"


@mcp.tool()
async def get_users(limit: int = 5) -> str:
    """Retrieve ServiceNow users (sys_user table).
    Args:
        limit: Number of users to retrieve (default 5, max 100).
    Returns:
        A formatted string with user details.
    """
    try:
        if limit > 100:
            limit = 100
        result = await sn_get("sys_user", limit=limit)
        
        if not result or "result" not in result:
            return "No users found or error retrieving users."
        
        users = result["result"]
        if not users:
            return "No users found."
        
        formatted_users = []
        for user in users:
            formatted_users.append(
                f"• {user.get('user_name', 'N/A')}: {user.get('name', 'No name')} "
                f"(Email: {user.get('email', 'N/A')}, Active: {user.get('active', 'N/A')})"
            )
        
        return f"Retrieved {len(users)} users:\n" + "\n".join(formatted_users)
    except ValueError as e:
        return f"Error retrieving users: {e}"

# --- Run the Server ---
if __name__ == "__main__":
    # # This allows running the server directly using `python server.py`
    # # The `mcp` command-line tool can also run this file.
    # # Transport defaults to 'stdio' when run directly like this.
    # mcp.run()
    mcp.tool()
