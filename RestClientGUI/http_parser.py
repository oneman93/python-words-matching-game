"""
HTTP File Parser for REST Client files (.http format)
Parses Teams.http file and extracts API endpoints with their details.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ApiEndpoint:
    """Represents an API endpoint from the HTTP file."""
    method: str  # GET, POST, PATCH, DELETE, etc.
    url: str  # URL with variables substituted
    original_url: str = ""  # Original URL with {{variables}}
    description: str = ""
    headers: Dict[str, str] = None
    body: str = ""
    line_number: int = 0
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if not self.original_url:
            self.original_url = self.url
    
    def __str__(self):
        return f"{self.method} {self.url}"
    
    def get_display_name(self) -> str:
        """Get a display name for the endpoint (shows original URL with variables)."""
        return f"{self.method} {self.original_url}"


class HttpParser:
    """Parser for REST Client HTTP files."""
    
    # HTTP methods to look for
    HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.variables: Dict[str, str] = {}
        self.endpoints: List[ApiEndpoint] = []
    
    def parse(self) -> List[ApiEndpoint]:
        """Parse the HTTP file and return list of API endpoints."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # First pass: Extract variables
        self._extract_variables(lines)
        
        # Second pass: Extract endpoints
        self._extract_endpoints(lines)
        
        return self.endpoints
    
    def _extract_variables(self, lines: List[str]):
        """Extract variable definitions (@variable_name=value)."""
        for line in lines:
            line = line.strip()
            if line.startswith('@') and '=' in line:
                # Extract variable name and value
                match = re.match(r'@(\w+)\s*=\s*(.+)', line)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    self.variables[var_name] = var_value
    
    def _extract_endpoints(self, lines: List[str]):
        """Extract API endpoints from the file."""
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line starts with an HTTP method
            method = None
            for http_method in self.HTTP_METHODS:
                if line.startswith(http_method + ' '):
                    method = http_method
                    break
            
            if method:
                # Extract URL (everything after method until end of line or space)
                url_match = re.match(rf'{method}\s+(.+)', line)
                if url_match:
                    original_url = url_match.group(1).strip()
                    
                    # Keep original URL, then substitute variables for actual request
                    substituted_url = self._substitute_variables(original_url)
                    
                    # Look for description in preceding comment lines
                    description = self._extract_description(lines, i)
                    
                    # Extract headers and body from following lines
                    headers, body, next_index = self._extract_request_details(lines, i + 1)
                    
                    # Create endpoint
                    endpoint = ApiEndpoint(
                        method=method,
                        url=substituted_url,  # Use substituted URL for actual requests
                        original_url=original_url,  # Keep original for display
                        description=description,
                        headers=headers,
                        body=body,
                        line_number=i + 1
                    )
                    self.endpoints.append(endpoint)
                    
                    i = next_index
                    continue
            
            i += 1
    
    def _extract_description(self, lines: List[str], current_index: int) -> str:
        """Extract description from comment lines before the endpoint."""
        description_parts = []
        
        # Look backwards for comment lines
        i = current_index - 1
        while i >= 0:
            line = lines[i].strip()
            
            # Stop if we hit another HTTP method or a section separator
            if any(line.startswith(method + ' ') for method in self.HTTP_METHODS):
                break
            if line.startswith('###') and len(line) > 3 and line[3] != '#':
                # This is a section header, include it
                desc = line.replace('###', '').strip()
                if desc:
                    description_parts.insert(0, desc)
                break
            
            # Collect comment lines
            if line.startswith('###'):
                desc = line.replace('###', '').strip()
                if desc:
                    description_parts.insert(0, desc)
            elif line.startswith('#'):
                desc = line.replace('#', '').strip()
                if desc and not desc.startswith('@'):
                    description_parts.insert(0, desc)
            
            i -= 1
        
        return ' '.join(description_parts[:3])  # Limit to first 3 comment lines
    
    def _extract_request_details(self, lines: List[str], start_index: int) -> tuple:
        """Extract headers and body from lines following the endpoint definition."""
        headers = {}
        body_lines = []
        i = start_index
        in_body = False
        body_started = False
        headers_finished = False
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines at the start (before headers)
            if not stripped and not body_started and not headers_finished:
                i += 1
                continue
            
            # Check if we've hit the next endpoint or section
            if stripped.startswith('###') and len(stripped) > 3:
                # Check if it's a section header (multiple #)
                if not stripped.startswith('####'):
                    break
            
            # Check if next HTTP method starts
            if any(stripped.startswith(method + ' ') for method in self.HTTP_METHODS):
                break
            
            # Skip comment lines
            if stripped.startswith('#'):
                i += 1
                continue
            
            # Parse headers (before body starts)
            if not in_body and ':' in stripped and not stripped.startswith('{') and not stripped.startswith('['):
                # This looks like a header
                header_parts = stripped.split(':', 1)
                if len(header_parts) == 2:
                    header_name = header_parts[0].strip()
                    header_value = header_parts[1].strip()
                    headers[header_name] = self._substitute_variables(header_value)
                    headers_finished = True
            elif stripped.startswith('{') or stripped.startswith('['):
                # JSON body starting
                in_body = True
                body_started = True
                body_lines.append(line.rstrip())
                
                # Check if body is complete (closing brace/bracket)
                if stripped.endswith('}') or stripped.endswith(']'):
                    # Check if this is the end of the body
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not next_line or next_line.startswith('#'):
                            i += 1
                            break
            elif headers_finished and stripped and not in_body:
                # After headers, any non-empty, non-comment line is body content
                # This handles form-urlencoded data and other non-JSON bodies
                in_body = True
                body_started = True
                body_lines.append(line.rstrip())
                
                # For form-urlencoded or single-line bodies, check if next line is empty or comment
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not next_line or next_line.startswith('#'):
                        i += 1
                        break
            elif in_body:
                # Continue collecting body lines
                body_lines.append(line.rstrip())
                
                # Check if body is complete (for multi-line bodies)
                if stripped.endswith('}') or stripped.endswith(']'):
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not next_line or next_line.startswith('#'):
                            i += 1
                            break
            
            i += 1
        
        body = '\n'.join(body_lines) if body_lines else ""
        
        # Substitute variables in body
        if body:
            body = self._substitute_variables(body)
        
        return headers, body, i
    
    def _substitute_variables(self, text: str) -> str:
        """Substitute variables in text ({{variable_name}} or @variable_name)."""
        # Substitute {{variable_name}} format
        for var_name, var_value in self.variables.items():
            text = text.replace(f'{{{{{var_name}}}}}', var_value)
            text = text.replace(f'@{{{var_name}}}', var_value)
        
        return text
    
    def get_all_urls(self) -> List[str]:
        """Get list of all URLs from parsed endpoints."""
        return [endpoint.url for endpoint in self.endpoints]
    
    def get_endpoint_by_url(self, url: str) -> Optional[ApiEndpoint]:
        """Get endpoint by URL."""
        for endpoint in self.endpoints:
            if endpoint.url == url:
                return endpoint
        return None
