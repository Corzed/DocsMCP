# DocsMCP

A powerful Model Context Protocol (MCP) server that provides seamless access to documentation on various topics directly to your AI assistant.

## What is DocsMCP?

DocsMCP connects Claude and other MCP-compatible AI assistants to documentation, allowing them to:

- Retrieve documentation files
- Navigate directory structures intuitively
- Access information with proper context
- Cache frequently accessed content for improved performance

## Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/corzed/DocsMCP.git
cd DocsMCP
```

### Step 2: Install Dependencies

Install the required `fastmcp` package:

```bash
pip install fastmcp
```

### Step 4: Add DocsMCP to your MCP Client

```json
{
  "mcpServers": {
    "DocsMCP": {
      "command": "python",
      "args": [
        "/absolute/path/to/DocsMCP.py"
      ]
    }
  }
}
```
