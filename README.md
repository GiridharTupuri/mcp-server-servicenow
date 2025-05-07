# 🚀 ServiceNow MCP Server

<div align="center">
  <img src="images/light.png" alt="MCP Architecture" width="400"/>
  <p><em>ServiceNow Integration for Model Context Protocol</em></p>
</div>

## 📋 Overview

This repository contains a ServiceNow integration server for the Model Context Protocol (MCP). It enables seamless interaction between ServiceNow instances and AI models through a standardized protocol, allowing for automated incident management, knowledge base article creation, and other ServiceNow operations.

## ✨ Features

- 🔌 **ServiceNow Integration**: Direct integration with ServiceNow instances
- 🛠️ **Multiple Operations Support**:
  - Create and manage incidents
  - Create knowledge base articles
  - Create client scripts
  - Create business rules
  - Create SLA definitions
  - Create record producers
- 🔒 **Secure Authentication**: Environment-based credentials management
- 🚀 **FastAPI-based Server**: High-performance async operations

## 🛠️ Prerequisites

- Python 3.12 or higher
- ServiceNow instance with appropriate API access
- Valid ServiceNow credentials
- Optional: Gemini API key for AI capabilities
- UV icorn for running the server
- FastAPI for building the server

## ⚙️ Configuration

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/mcp-server-now.git
   cd mcp-server-now
   ```

2. Create a `.env` file with your credentials:

   ```
   SERVICENOW_INSTANCE=https://your-instance.service-now.com
   SERVICENOW_USERNAME=your_username
   SERVICENOW_PASSWORD=your_password
   GEMINI_API_KEY=your_api_key  # Optional
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## 🚀 Getting Started

### Running the Server

```bash
mcp install <file_name>.py
```

### Example Usage

The server provides several tools for ServiceNow operations. Here are some examples:

1. **Create an Incident**:

   ```python
   create_incident(
       short_description="Network outage in building B",
       description="Users reporting connectivity issues",
       urgency="2",
       impact="2"
   )
   ```

2. **Create a Knowledge Base Article**:
   ```python
   create_kb_article(
       short_description="How to Reset Your Password",
       article_body="<h1>Password Reset Instructions</h1><p>1. Navigate to the login page</p>",
       workflow_state="published"
   )
   ```

For more examples, see [servicenow-test-examples.md](servicenow-test-examples.md).

## 🧩 Available Tools

The server provides the following tools:

- `create_incident`: Create new incidents
- `create_kb_article`: Create knowledge base articles
- `create_client_script`: Create client-side scripts
- `create_business_rule`: Create business rules
- `create_sla_definition`: Create SLA definitions
- `create_record_producer`: Create record producers with customizable variables
- `create_variable_set`: Create reusable variable sets for catalog items

### Record Producer Details

The `create_record_producer` tool allows you to create ServiceNow record producers with the following features:

```python
create_record_producer(
    name="Report Network Issue",
    table_name="incident",
    short_description="Use this form to report network connectivity issues",
    category_sys_id="optional_category_sys_id",
    script="optional_server_side_script",
    variables=[
        {
            "name": "issue_type",
            "label": "Type of Issue",
            "type": "choice",
            "choices": ["Connectivity", "Performance", "Access"],
            "mandatory": True
        },
        {
            "name": "affected_users",
            "label": "Number of Affected Users",
            "type": "integer",
            "mandatory": True
        }
    ]
)
```

Key features:

- Customizable form fields with various types (string, integer, boolean, reference, etc.)
- Server-side scripting support
- Category assignment
- Mandatory field configuration
- Default values and help text

### Variable Sets

The `create_variable_set` tool allows you to create reusable variable sets that can be attached to multiple catalog items:

```python
create_variable_set(
    name="Hardware Request Variables",
    description="Common variables for hardware requests",
    variables=[
        {
            "name": "device_type",
            "label": "Device Type",
            "type": "choice",
            "choices": ["Laptop", "Desktop", "Tablet", "Phone"],
            "mandatory": True
        },
        {
            "name": "justification",
            "label": "Justification",
            "type": "text",
            "mandatory": True,
            "help_text": "Please explain why you need this hardware"
        }
    ]
)
```

Variable sets support:

- Multiple variable types (string, integer, boolean, reference, choice, etc.)
- Custom validation rules
- Help text and descriptions
- Mandatory field configuration
- Default values
- Reference fields to other ServiceNow tables

## 🔧 Development

### Project Structure

```
mcp-server-now/
├── servicenow.py          # Main server implementation
├── servicenow-test-examples.md  # Example usage
├── pyproject.toml         # Project configuration
├── .env                   # Environment variables
└── README.md             # This file
```

### Adding New Tools

To add new ServiceNow operations:

1. Create a new async function in `servicenow.py`
2. Decorate it with `@mcp.tool()`
3. Add proper documentation and error handling
4. Test the new functionality

## 📚 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/introduction)
- [ServiceNow REST API Documentation](https://modelcontextprotocol.io/quickstart/server)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please:

- Open an issue in this repository
- Contact the maintainers
- Check the [ServiceNow documentation](https://docs.servicenow.com)

## 👤 Author

<div align="center">
  <img src="https://github.com/divyashah0510.png" alt="Divya Shah" width="200" style="border-radius:50%;"/>
  <p><strong>Divya Shah</strong></p>
  <p>
   AI Engineer | ServiceNow Developer | Open Source Contributor
  </p>
  <p>
    <a href="https://github.com/divyashah0510">GitHub</a> •
    <a href="https://linkedin.com/in/divya-d-shah">LinkedIn</a> •
    <a href="https://x.com/Divya_Shah22">Twitter</a>
  </p>
</div>

---

## Live Demo

<iframe width="560" height="315" src="https://www.youtube.com/embed/FojEOrdFWxo?si=WQZoNOwEe_ktaiJ_" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

<div align="center">
  <p>Made with ❤️ by Divya Shah</p>
</div>
