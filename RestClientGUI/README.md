# REST Client GUI

A Python Tkinter-based GUI application for executing HTTP requests from REST Client files (`.http` format).

## Features

- **Parse HTTP Files**: Automatically parses REST Client format files (like Teams.http)
- **Dropdown List**: Browse all API endpoints from the parsed file
- **Search Filter**: Filter endpoints by URL, method, or description
- **Execute Requests**: Run HTTP requests (GET, POST, PUT, PATCH, DELETE, etc.)
- **Response Viewer**: View formatted responses with syntax highlighting
- **Search in Response**: Use Ctrl-F to search within response text

## Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- requests library

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

The application will automatically look for the Teams.http file at:
- `../Informatica-API-RestClient/API (Rest Client)/Teams.http`

If the file is in a different location, modify the path in `main.py`.

## Features in Detail

### 1. Search Filter
- Type in the search box to filter the dropdown list
- Filters by URL, HTTP method, or description
- Updates in real-time as you type

### 2. API Endpoint Dropdown
- Shows all parsed endpoints from the HTTP file
- Format: `METHOD URL - Description`
- Select an endpoint to view its details

### 3. Run Button
- Executes the selected HTTP request
- Shows status in the status bar
- Displays formatted response in the text area

### 4. Response Viewer
- Shows HTTP status code and reason
- Displays response headers
- Formats JSON responses with indentation
- Scrollable text area

### 5. Search in Response (Ctrl-F)
- Press Ctrl-F while the response text area is focused
- Opens a search dialog
- Find Next/Previous buttons to navigate matches
- Case-insensitive search

## Project Structure

```
RestClientGUI/
├── main.py              # Entry point
├── rest_client_gui.py   # Main GUI application
├── http_parser.py      # HTTP file parser
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## How It Works

1. **HTTP Parser** (`http_parser.py`):
   - Parses REST Client format files
   - Extracts HTTP methods, URLs, headers, and request bodies
   - Handles variable substitution (`{{variable_name}}`)
   - Extracts descriptions from comments

2. **GUI Application** (`rest_client_gui.py`):
   - Creates Tkinter interface
   - Manages endpoint selection and filtering
   - Executes HTTP requests using `requests` library
   - Formats and displays responses

3. **Main Entry Point** (`main.py`):
   - Locates the HTTP file
   - Initializes and runs the GUI

## Supported HTTP Methods

- GET
- POST
- PUT
- PATCH
- DELETE
- HEAD
- OPTIONS

## Notes

- Variables defined in the HTTP file (e.g., `@team_id=value`) are automatically substituted in URLs and headers
- JSON request bodies are automatically formatted
- The application handles both JSON and form-encoded request bodies
- Response timeout is set to 30 seconds

## Troubleshooting

**File Not Found Error:**
- Ensure the Teams.http file exists at the expected path
- Modify the path in `main.py` if needed

**Import Errors:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Ensure Python 3.7+ is being used

**Request Errors:**
- Check that the endpoint URL is correct
- Verify authentication tokens are valid
- Check network connectivity
