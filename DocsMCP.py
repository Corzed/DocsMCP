from fastmcp import FastMCP
import urllib.request
import urllib.parse
import json
import time

class Cache:
    def __init__(self, ttl=3600):  # TTL in seconds (1 hour default)
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        current_time = time.time()
        
        # Check if entry has decayed (expired)
        if current_time - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None
            
        return entry['data']
    
    def set(self, key, data):
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

class DocsMCP:
    def __init__(self, name="DocsMCP", repo="Corzed/Docs", branch="master"):
        self.mcp = FastMCP(name=name)
        self.root_url = f"https://cdn.jsdelivr.net/gh/{repo}@{branch}"
        self.docs_url = f"{self.root_url}/docs"
        self.cache = Cache()
        self.site_structure = None
        
        # Register tools
        self.mcp.tool(name="get_docs", description="Get documents or list directories")(self.get_docs)
        self.mcp.tool(name="list_directory", description="List contents of a directory")(self.list_directory)
    
    def fetch_url(self, url):
        """Fetch content from a URL with decay-based caching"""
        cached_content = self.cache.get(url)
        if cached_content:
            return cached_content
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DocsMCP/1.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                self.cache.set(url, content)
                return content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_docs(self, path: str = "") -> str:
        """Get document content"""
        clean_path = path.strip('/')
        encoded_path = '/'.join(urllib.parse.quote(component) for component in clean_path.split('/'))
        url = f"{self.docs_url}/{encoded_path}"
        
        content = self.fetch_url(url)
        return f"Content of '{path}':\n\n{content}"
    
    def get_structure(self):
        """Load the site structure once and cache it"""
        if not self.site_structure:
            content = self.fetch_url(f"{self.root_url}/_site_structure.json")
            try:
                self.site_structure = json.loads(content)
            except:
                return None
        return self.site_structure
    
    def list_directory(self, path: str = "") -> str:
        """List contents of a directory using the site structure"""
        structure = self.get_structure()
        if not structure:
            return "Error: Could not load site structure"
        
        # Navigate to requested directory
        current = structure
        for part in filter(None, path.split('/')):
            if part in current.get('children', {}):
                current = current['children'][part]
            else:
                return f"Directory not found: {path}"
        
        # List contents
        result = f"Contents of '{path}':\n\n"
        for name, item in current.get('children', {}).items():
            prefix = "📁 " if item["type"] == "directory" else "📄 "
            title = item.get('title', name)
            result += f"{prefix} {name} - {title}\n"
        
        return result
    
    def run(self):
        """Run the MCP server"""
        self.mcp.run(transport='stdio')

if __name__ == "__main__":
    DocsMCP().run()
