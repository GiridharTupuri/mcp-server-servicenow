# ServiceNow MCP Functions - Testing Examples

## Prerequisites
1. Ensure your `.env` file is properly set up with:
   ```
   SERVICENOW_INSTANCE=https://your-instance.service-now.com
   SERVICENOW_USERNAME=your_username
   SERVICENOW_PASSWORD=your_password
   GEMINI_API_KEY=your_api_key  # Optional
   ```
2. Make sure your ServiceNow instance is accessible
3. Ensure the user has appropriate permissions for all operations

## 1. Create Incident
Test creating incidents with various priorities and details:

```
create_incident short_description="Network outage in building B"
```

```
create_incident short_description="Email server not responding" description="Users in marketing department cannot send or receive emails since 9:30 AM." urgency="2" impact="2"
```

```
create_incident short_description="Production database down" description="The main production database is not responding, affecting all customer transactions." urgency="1" impact="1" caller_id="admin"
```

## 2. Create Knowledge Base Article
Test creating KB articles with different content:

```
create_kb_article short_description="How to Reset Your Password" article_body="<h1>Password Reset Instructions</h1><p>1. Navigate to the login page</p><p>2. Click on 'Forgot Password'</p><p>3. Follow the email instructions</p>"
```

```
create_kb_article short_description="VPN Connection Troubleshooting" article_body="Common VPN issues and their solutions..." workflow_state="draft"
```

```
create_kb_article short_description="New Expense Report Process" article_body="Starting June 1st, all expense reports must be submitted through the new portal..." kb_knowledge_base="IT" workflow_state="published"
```

## 3. Create Client Script
Test creating client scripts for different events:

```
create_client_script name="Validate Priority" table="incident" script="function onChange(control, oldValue, newValue, isLoading) {\n  if (isLoading) return;\n  if (newValue == '1') {\n    alert('High priority selected - please provide detailed description');\n  }\n}" script_type="onChange" field_name="priority"
```

```
create_client_script name="Prefill Caller Information" table="incident" script="function onLoad() {\n  var user = g_user.userID;\n  g_form.setValue('caller_id', user);\n}" script_type="onLoad"
```

```
create_client_script name="Confirm Incident Submission" table="incident" script="function onSubmit() {\n  return confirm('Are you sure you want to submit this incident?');\n}" script_type="onSubmit"
```

## 4. Create Business Rule
Test creating business rules for different scenarios:

```
create_business_rule name="Auto-assign P1 Incidents" table="incident" script="(function executeRule(current, previous /*null when async*/) {\n  if (current.priority == '1') {\n    current.assigned_to = 'helpdesk';\n    current.assignment_group = 'p1_response_team';\n  }\n})(current, previous);" when="before"
```

```
create_business_rule name="Notify Manager on Expense Report" table="expense_report" script="(function executeRule(current, previous /*null when async*/) {\n  var manager = current.requested_for.manager;\n  gs.eventQueue('expense.submitted', current, current.number, manager);\n})(current, previous);" when="after" action_insert="true" action_update="false"
```

```
create_business_rule name="Validate Change Approval" table="change_request" script="(function executeRule(current, previous /*null when async*/) {\n  if (current.state == 'implement' && !current.approval.nil() && current.approval != 'approved') {\n    gs.addErrorMessage('Change must be approved before implementation');\n    current.setAbortAction(true);\n  }\n})(current, previous);" when="before" action_update="true" action_insert="false"
```

## 5. Create SLA Definition
Test creating SLA definitions with different durations and conditions:

```
create_sla_definition name="P1 Incident Response" table="incident" duration_seconds="1800" start_condition="priority=1^active=true" stop_condition="assigned_to!=NULL"
```

```
create_sla_definition name="Hardware Request Fulfillment" table="sc_req_item" duration_seconds="172800" start_condition="cat_item.name=Hardware^active=true" stop_condition="state=closed"
```

```
create_sla_definition name="VIP Incident Resolution" table="incident" duration_seconds="14400" start_condition="caller_id.vip=true^active=true" stop_condition="state=resolved" pause_condition="awaiting_user_info=true"
```

## 6. Create Record Producer
Test creating record producers with different configurations:

```
create_record_producer name="Report Network Issue" table_name="incident" short_description="Use this form to report network connectivity issues" variables=[{"name":"issue_type","label":"Type of Issue","type":"choice","choices":["Connectivity","Performance","Access"],"mandatory":true},{"name":"affected_users","label":"Number of Affected Users","type":"integer","mandatory":true}]
```

```
create_record_producer name="New Equipment Request" table_name="sc_req_item" short_description="Request new hardware or equipment" category_sys_id="e0d08b13c3330100c8b837659bba8fb4" variables=[{"name":"device_type","label":"Device Type","type":"choice","choices":["Laptop","Desktop","Tablet","Phone"],"mandatory":true},{"name":"justification","label":"Justification","type":"text","mandatory":true,"help_text":"Please explain why you need this hardware"}]
```

```
create_record_producer name="Building Access Request" table_name="sc_request" short_description="Request building access for new employees" script="current.short_description = 'Building Access for ' + current.variables.employee_name;\ncurrent.assignment_group = 'facilities';" variables=[{"name":"employee_name","label":"Employee Name","type":"string","mandatory":true},{"name":"access_type","label":"Type of Access","type":"choice","choices":["Full Access","Restricted Access","Temporary Access"],"mandatory":true}]
```

## 7. Create Variable Set
Test creating variable sets for different use cases:

```
create_variable_set name="Hardware Request Variables" description="Common variables for hardware requests" variables=[
  {
    "name": "device_type",
    "label": "Device Type",
    "type": "choice",
    "choices": ["Laptop", "Desktop", "Tablet", "Phone"],
    "mandatory": true
  },
  {
    "name": "justification",
    "label": "Justification",
    "type": "text",
    "mandatory": true,
    "help_text": "Please explain why you need this hardware"
  }
]
```

```
create_variable_set name="Employee Onboarding Variables" description="Variables for new employee onboarding" variables=[
  {
    "name": "start_date",
    "label": "Start Date",
    "type": "date",
    "mandatory": true
  },
  {
    "name": "department",
    "label": "Department",
    "type": "reference",
    "reference_table": "cmn_department",
    "mandatory": true
  },
  {
    "name": "equipment_needed",
    "label": "Required Equipment",
    "type": "boolean",
    "default_value": true
  }
]
```

```
create_variable_set name="IT Support Variables" description="Common variables for IT support requests" variables=[
  {
    "name": "issue_category",
    "label": "Issue Category",
    "type": "choice",
    "choices": ["Hardware", "Software", "Network", "Access"],
    "mandatory": true
  },
  {
    "name": "urgency",
    "label": "Urgency Level",
    "type": "choice",
    "choices": ["Low", "Medium", "High", "Critical"],
    "mandatory": true
  },
  {
    "name": "description",
    "label": "Issue Description",
    "type": "text",
    "mandatory": true,
    "help_text": "Please provide detailed description of the issue"
  },
  {
    "name": "affected_location",
    "label": "Affected Location",
    "type": "reference",
    "reference_table": "cmn_location",
    "mandatory": false
  },
  {
    "name": "business_impact",
    "label": "Business Impact",
    "type": "select_box",
    "choices": ["No Impact", "Low Impact", "Medium Impact", "High Impact", "Critical Impact"],
    "mandatory": false,
    "help_text": "Select the level of business impact this issue is causing"
  }
]
```
