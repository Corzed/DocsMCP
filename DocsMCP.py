from fastmcp import FastMCP
import urllib.request
import urllib.parse
import json
import time
import re

class Cache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache and time.time() - self.cache[key]['timestamp'] <= self.ttl:
            return self.cache[key]['data']
        return None
    
    def set(self, key, data):
        self.cache[key] = {'data': data, 'timestamp': time.time()}

class DocsMCP:
    def __init__(self, name="DocsMCP", repo="Corzed/Docs", branch="master"):
        self.mcp = FastMCP(name=name)
        self.repo = repo
        self.branch = branch
        self.root_url = f"https://cdn.jsdelivr.net/gh/{repo}@{branch}"
        self.cache = Cache()
        self.site_structure = None
        
        self.mcp.tool(name="get_docs", description="Get documents or list directories")(self.get_docs)
        self.mcp.tool(name="list_directory", description="List contents of a directory")(self.list_directory)
    
    def normalize_path(self, path):
        path = path.strip().strip('/')
        path = re.sub(r'/+', '/', path)
        path = re.sub(r'\s*/\s*', '/', path)
        parts = [part.strip() for part in path.split('/')]
        return '/'.join(filter(None, parts))
    
    def fetch_url(self, url):
        cached = self.cache.get(url)
        if cached:
            return cached
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DocsMCP/1.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                self.cache.set(url, content)
                return content
        except:
            return None
    
    def is_file_path(self, path):
        if not path:
            return False
        
        path = self.normalize_path(path)
        structure = self.get_structure()
        current = structure
        
        for i, part in enumerate(path.split('/')):
            if part not in current.get("children", {}):
                return False
            
            if i == len(path.split('/')) - 1:
                return current["children"][part].get("type") == "file"
            
            current = current["children"][part]
        
        return False
    
    def get_docs(self, path=""):
        clean_path = self.normalize_path(path)
        
        if not clean_path:
            return "Error: Empty path. Use list_directory to see available directories."
        
        if not self.is_file_path(clean_path):
            return f"Error: '{path}' is not a valid document. Use list_directory to navigate."
        
        parts = clean_path.split('/')
        encoded_parts = [urllib.parse.quote(part) for part in parts]
        url = f"{self.root_url}/docs/{'/'.join(encoded_parts)}"
        content = self.fetch_url(url)
        
        if not content:
            return f"Error: Could not fetch document at '{path}'"
        
        return f"Content of '{path}':\n\n{content}"
    
    def get_structure(self):
        if self.site_structure:
            return self.site_structure
        
        api_url = f"https://data.jsdelivr.com/v1/package/gh/{self.repo}@{self.branch}/flat"
        content = self.fetch_url(api_url)
        
        if not content:
            return {"children": {}}
        
        try:
            file_list = json.loads(content)
            structure = {"children": {}}
            
            for file in file_list.get("files", []):
                path = file.get("name", "")
                
                if not path.startswith("/docs/"):
                    continue
                
                logical_path = self.normalize_path(path[6:])
                if not logical_path:
                    continue
                
                parts = logical_path.split('/')
                current = structure
                
                for i, part in enumerate(parts):
                    is_file = (i == len(parts) - 1)
                    
                    if is_file:
                        current["children"][part] = {"type": "file"}
                    else:
                        if part not in current["children"]:
                            current["children"][part] = {"type": "directory", "children": {}}
                        current = current["children"][part]
            
            self.site_structure = structure
            return structure
        except:
            return {"children": {}}
    
    def list_directory(self, path=""):
        clean_path = self.normalize_path(path)
        structure = self.get_structure()
        current = structure
        
        if clean_path:
            for part in clean_path.split('/'):
                if part not in current.get("children", {}):
                    return f"Directory not found: {path}"
                current = current["children"][part]
                if current.get("type") != "directory":
                    return f"Error: '{path}' is a file, not a directory"
        
        result = f"Contents of '{path}':\n\n"
        items = sorted(current.get("children", {}).items())
        
        if not items:
            return result + "Directory is empty"
        
        for name, item in items:
            prefix = "📁 " if item.get("type") == "directory" else "📄 "
            result += f"{prefix} {name}\n"
        
        return result
    
    def run(self):
        self.mcp.run(transport='stdio')

if __name__ == "__main__":
    DocsMCP().run()
