#!/usr/bin/env python3
"""
Universal Scraper Sandbox Executor
Supports: Node.js, Python, Deno, Go, Ruby, CLI scripts
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler

API_KEY = os.environ.get('API_KEY', '')

class LanguageDetector:
    """Auto-detect programming language and entry point"""
    
    @staticmethod
    def detect(repo_path: str, entry_point: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Returns: (runtime, entry_point, install_command)
        """
        repo = Path(repo_path)
        
        # If entry point is specified, try to detect from that
        if entry_point:
            entry_file = repo / entry_point
            if entry_file.exists():
                if entry_point.endswith('.js'):
                    return ('node', entry_point, 'npm install' if (repo / 'package.json').exists() else '')
                elif entry_point.endswith('.ts'):
                    return ('deno', entry_point, '')
                elif entry_point.endswith('.py'):
                    return ('python', entry_point, 'pip3 install -r requirements.txt' if (repo / 'requirements.txt').exists() else '')
                elif entry_point.endswith('.go'):
                    return ('go', entry_point, 'go mod download' if (repo / 'go.mod').exists() else '')
                elif entry_point.endswith('.rb'):
                    return ('ruby', entry_point, 'bundle install' if (repo / 'Gemfile').exists() else '')
        
        # Auto-detect from project files
        if (repo / 'package.json').exists():
            # Check for main entry in package.json
            try:
                with open(repo / 'package.json') as f:
                    pkg = json.load(f)
                    main = pkg.get('main', 'index.js')
                    return ('node', main, 'npm install')
            except:
                return ('node', 'index.js', 'npm install')
        
        if (repo / 'deno.json').exists() or (repo / 'deno.jsonc').exists():
            return ('deno', 'main.ts', '')
        
        if (repo / 'requirements.txt').exists():
            # Look for common Python entry points
            for name in ['main.py', 'scraper.py', 'app.py', 'run.py']:
                if (repo / name).exists():
                    return ('python', name, 'pip3 install -r requirements.txt')
            return ('python', 'main.py', 'pip3 install -r requirements.txt')
        
        if (repo / 'go.mod').exists():
            return ('go', 'main.go', 'go mod download')
        
        if (repo / 'Gemfile').exists():
            return ('ruby', 'main.rb', 'bundle install')
        
        # Fallback: look for common entry point files
        for name in ['index.js', 'main.js', 'scraper.js']:
            if (repo / name).exists():
                return ('node', name, 'npm install' if (repo / 'package.json').exists() else '')
        
        for name in ['main.py', 'scraper.py']:
            if (repo / name).exists():
                return ('python', name, 'pip3 install -r requirements.txt' if (repo / 'requirements.txt').exists() else '')
        
        raise ValueError("Could not detect programming language or entry point")


class ScraperExecutor:
    """Execute scrapers in various runtimes"""
    
    @staticmethod
    def execute(runtime: str, entry_point: str, repo_path: str, install_cmd: str, run_cmd: Optional[str] = None) -> Dict:
        """Execute the scraper and return results"""
        
        results = {
            'success': False,
            'stdout': '',
            'stderr': '',
            'runtime': runtime,
            'entry_point': entry_point
        }
        
        try:
            # Change to repo directory
            os.chdir(repo_path)
            
            # Install dependencies if needed
            if install_cmd:
                print(f"Installing dependencies: {install_cmd}")
                install_result = subprocess.run(
                    install_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout for installs
                )
                
                if install_result.returncode != 0:
                    results['stderr'] = f"Install failed: {install_result.stderr}"
                    return results
            
            # Execute the scraper
            if run_cmd:
                cmd = run_cmd
            else:
                cmd = ScraperExecutor._get_run_command(runtime, entry_point)
            
            print(f"Executing: {cmd}")
            exec_result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for execution
            )
            
            results['stdout'] = exec_result.stdout
            results['stderr'] = exec_result.stderr
            results['success'] = exec_result.returncode == 0
            
        except subprocess.TimeoutExpired:
            results['stderr'] = "Execution timed out"
        except Exception as e:
            results['stderr'] = str(e)
        
        return results
    
    @staticmethod
    def _get_run_command(runtime: str, entry_point: str) -> str:
        """Get the default run command for a runtime"""
        commands = {
            'node': f'node {entry_point}',
            'python': f'python3 {entry_point}',
            'deno': f'deno run --allow-all {entry_point}',
            'go': f'go run {entry_point}',
            'ruby': f'ruby {entry_point}'
        }
        return commands.get(runtime, entry_point)


class SandboxHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the sandbox API"""
    
    def _send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """Handle scraper execution requests"""
        
        # Authenticate
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer ') or auth_header[7:] != API_KEY:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
            return
        
        try:
            # Parse request
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            repo_url = data.get('repoUrl')
            entry_point = data.get('entryPoint')
            install_cmd = data.get('installCmd')
            run_cmd = data.get('runCmd')
            
            if not repo_url:
                raise ValueError("repoUrl is required")
            
            # Create temp directory for this scraper
            temp_dir = tempfile.mkdtemp(prefix='scraper_', dir='/tmp/scrapers')
            
            try:
                # Clone repository
                print(f"Cloning {repo_url} to {temp_dir}")
                clone_result = subprocess.run(
                    ['git', 'clone', repo_url, temp_dir],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if clone_result.returncode != 0:
                    raise Exception(f"Clone failed: {clone_result.stderr}")
                
                # Detect language and entry point
                runtime, detected_entry, detected_install = LanguageDetector.detect(
                    temp_dir,
                    entry_point
                )
                
                # Use provided commands if available, otherwise use detected
                final_entry = entry_point or detected_entry
                final_install = install_cmd or detected_install
                
                print(f"Detected: runtime={runtime}, entry={final_entry}, install={final_install}")
                
                # Execute the scraper
                results = ScraperExecutor.execute(
                    runtime=runtime,
                    entry_point=final_entry,
                    repo_path=temp_dir,
                    install_cmd=final_install,
                    run_cmd=run_cmd
                )
                
                # Send response
                self.send_response(200 if results['success'] else 500)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
                
            finally:
                # Cleanup
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'success': False
            }).encode())
    
    def do_GET(self):
        """Health check endpoint"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'healthy',
                'service': 'universal-sandbox'
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), SandboxHandler)
    print(f"Universal sandbox listening on port {port}")
    server.serve_forever()

