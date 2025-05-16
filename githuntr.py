#!/usr/bin/env python3
"""
GitHuntr - Multi-platform GitHub search tool
"""

import os
import re
import json
import math
import shutil
import tempfile
import argparse
from pathlib import Path
from typing import List, Dict, Set, Optional, Union
from datetime import datetime
import git
import numpy as np
from tqdm import tqdm
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()

class EntropyCalculator:
    """Handles entropy-based secret detection in text."""
    
    BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="  # Removed type annotation for 3.6 compatibility
    
    @staticmethod
    def calculate_entropy(text: str) -> float:
        """
        Calculate Shannon entropy of a string.
        
        Args:
            text: Input string
            
        Returns:
            float: Entropy value
        """
        if not text:
            return 0.0
            
        # Count character frequencies
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
            
        # Calculate entropy
        length = len(text)
        return -sum(count/length * math.log2(count/length) for count in freq.values())
    
    @classmethod
    def scan_for_secrets(cls, content: str) -> List[str]:
        """
        Scan text content for potential secrets using entropy analysis.
        
        Args:
            content: Text content to scan
            
        Returns:
            List[str]: List of potential secrets found
        """
        secrets = []
        words = re.split(r'[\s:=]+', content)
        
        for word in words:
            word = word.strip()
            if len(word) > 15:  # Only check strings that could be secrets
                # Calculate entropy only for strings with base64 characters
                if all(c in cls.BASE64_CHARS for c in word):
                    entropy = cls.calculate_entropy(word)
                    if entropy > 4.3:  # Threshold from original implementation
                        secrets.append(word)
                        
        return secrets

class GitHuntr:
    """Main class for GitHub repository scanning."""
    
    def __init__(self, repo_url: str, temp_dir: Optional[str] = None, max_commits: Optional[int] = None):
        """
        Initialize GitHuntr instance.
        
        Args:
            repo_url: URL of the GitHub repository
            temp_dir: Optional temporary directory path
            max_commits: Maximum number of commits to search through (None for all)
        """
        self.repo_url = repo_url
        self.repo_name = repo_url.split('/')[-1]
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix='githuntr-')
        self.repo = None
        self.branches = []
        self.max_commits = max_commits
        self.results = {
            'repo': repo_url,
            'branches': {},
            'commit_history': {}
        }
        
    def clone_repo(self) -> None:
        """Clone the repository and get list of branches."""
        print(f"{Fore.CYAN}Cloning repository {self.repo_url}...{Style.RESET_ALL}")
        try:
            self.repo = git.Repo.clone_from(self.repo_url, self.temp_dir)
        except git.exc.GitCommandError as e:
            if "Authentication failed" in str(e):
                print(f"{Fore.RED}Authentication Error: Could not access repository.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Make sure you have:")
                print("1. Valid GitHub authentication set up in your terminal")
                print("2. Access rights to the repository")
                print("3. Using the correct repository URL (HTTPS or SSH matching your auth method){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Error cloning repository. Make sure git is installed and the URL is correct.{Style.RESET_ALL}")
            raise e
        
        # Get all remote branches
        for ref in self.repo.remote().refs:
            branch_name = ref.name.split('/')[-1]
            if branch_name != 'HEAD':
                self.branches.append(branch_name)
                
        print(f"{Fore.GREEN}Found {len(self.branches)} branches{Style.RESET_ALL}")
        
    def search_branch(self, branch: str, filename_regex: Optional[Union[str, re.Pattern]], 
                     content_regex: Optional[Union[str, re.Pattern]], do_entropy: bool) -> Dict:
        """
        Search a specific branch for matches.
        
        Args:
            branch: Branch name to search
            filename_regex: Regex pattern for filenames
            content_regex: Regex pattern for file contents
            do_entropy: Whether to perform entropy analysis
            
        Returns:
            Dict: Search results for the branch
        """
        print(f"\n{Fore.CYAN}Searching branch: {branch}{Style.RESET_ALL}")
        
        # Checkout branch
        try:
            self.repo.git.checkout(branch)
        except git.exc.GitCommandError:
            print(f"{Fore.YELLOW}Warning: Could not checkout branch {branch}. Skipping...{Style.RESET_ALL}")
            return {'filenames': [], 'content': {}, 'entropy': {}}
        
        branch_results = {
            'filenames': [],
            'content': {},
            'entropy': {}
        }
        
        # Walk through all files in the repository
        for root, _, files in os.walk(self.temp_dir):
            if '.git' in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.temp_dir)
                
                # Check filename match
                if filename_regex and re.search(filename_regex, file):
                    branch_results['filenames'].append(rel_path)
                    
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check content match
                    if content_regex and re.search(content_regex, content):
                        matches = re.findall(content_regex, content)
                        branch_results['content'][rel_path] = matches
                        
                    # Perform entropy scan
                    if do_entropy:
                        secrets = EntropyCalculator.scan_for_secrets(content)
                        if secrets:
                            branch_results['entropy'][rel_path] = secrets
                            
                except (UnicodeDecodeError, IOError):
                    continue  # Skip binary files and files we can't read
                    
        return branch_results
        
    def search_commit(self, commit: git.Commit, filename_regex: Optional[Union[str, re.Pattern]], 
                     content_regex: Optional[Union[str, re.Pattern]], do_entropy: bool) -> Dict:
        """
        Search a specific commit for matches.
        
        Args:
            commit: Git commit to search
            filename_regex: Regex pattern for filenames
            content_regex: Regex pattern for file contents
            do_entropy: Whether to perform entropy analysis
            
        Returns:
            Dict: Search results for the commit
        """
        commit_results = {
            'filenames': [],
            'content': {},
            'entropy': {},
            'commit_info': {
                'hash': commit.hexsha,
                'author': commit.author.name,
                'date': datetime.fromtimestamp(commit.authored_date).isoformat(),
                'message': commit.message.strip()
            }
        }
        
        try:
            # Get the list of files in this commit
            for blob in commit.tree.traverse():
                if not blob.type == 'blob':  # Skip if not a file
                    continue
                    
                # Check filename match
                if filename_regex and re.search(filename_regex, blob.name):
                    commit_results['filenames'].append(blob.path)
                
                try:
                    # Get file content
                    content = blob.data_stream.read().decode('utf-8')
                    
                    # Check content match
                    if content_regex and re.search(content_regex, content):
                        matches = re.findall(content_regex, content)
                        commit_results['content'][blob.path] = matches
                        
                    # Perform entropy scan
                    if do_entropy:
                        secrets = EntropyCalculator.scan_for_secrets(content)
                        if secrets:
                            commit_results['entropy'][blob.path] = secrets
                            
                except (UnicodeDecodeError, IOError):
                    continue  # Skip binary files and files we can't read
                    
        except git.exc.GitCommandError:
            print(f"{Fore.YELLOW}Warning: Could not analyze commit {commit.hexsha[:8]}{Style.RESET_ALL}")
            
        return commit_results

    def search_history(self, filename_regex: Optional[Union[str, re.Pattern]], 
                      content_regex: Optional[Union[str, re.Pattern]], 
                      do_entropy: bool) -> None:
        """
        Search through commit history for matches.
        
        Args:
            filename_regex: Regex pattern for filenames
            content_regex: Regex pattern for file contents
            do_entropy: Whether to perform entropy analysis
        """
        print(f"\n{Fore.CYAN}Searching through commit history...{Style.RESET_ALL}")
        
        # Get all commits
        commits = list(self.repo.iter_commits('--all'))
        if self.max_commits:
            commits = commits[:self.max_commits]
            
        # Search through commits
        for commit in tqdm(commits, desc="Analyzing commits"):
            results = self.search_commit(commit, filename_regex, content_regex, do_entropy)
            
            # Only add commits that have matches
            if (results['filenames'] or results['content'] or results['entropy']):
                self.results['commit_history'][commit.hexsha] = results

    def scan_repository(self, filename_regex: Optional[str] = None, 
                       content_regex: Optional[str] = None,
                       do_entropy: bool = False,
                       search_history: bool = False) -> Dict:
        """
        Scan the entire repository across all branches and optionally commit history.
        
        Args:
            filename_regex: Regex pattern for filenames
            content_regex: Regex pattern for file contents
            do_entropy: Whether to perform entropy analysis
            search_history: Whether to search through commit history
            
        Returns:
            Dict: Complete scan results
        """
        try:
            self.clone_repo()
            
            # Compile regex patterns
            if filename_regex:
                filename_regex = re.compile(filename_regex)
            if content_regex:
                content_regex = re.compile(content_regex)
            
            # Search each branch
            for branch in tqdm(self.branches, desc="Scanning branches"):
                branch_results = self.search_branch(
                    branch, filename_regex, content_regex, do_entropy
                )
                self.results['branches'][branch] = branch_results
                
            # Search through commit history if requested
            if search_history:
                self.search_history(filename_regex, content_regex, do_entropy)
                
            return self.results
            
        finally:
            # Cleanup
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                
def validate_regex(pattern: str, pattern_type: str) -> Optional[str]:
    """
    Validate and potentially fix a regex pattern.
    
    Args:
        pattern: The regex pattern to validate
        pattern_type: Type of pattern ('filename' or 'content') for error messages
        
    Returns:
        Optional[str]: Fixed pattern or None if invalid
    """
    if not pattern:
        return None
        
    # Convert glob-style patterns to regex
    if '*' in pattern and not any(c in pattern for c in '.^${}[]()'):
        pattern = pattern.replace('*', '.*')
    
    try:
        re.compile(pattern)
        return pattern
    except re.error as e:
        print(f"{Fore.RED}Invalid {pattern_type} regex pattern: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Tips for common patterns:")
        print("- For substring match: 'token'")
        print("- For wildcard match: '.*token.*'")
        print("- For file extensions: '.*\\.txt$'")
        print("- For exact match: '^token$'{Style.RESET_ALL}")
        return None

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='GitHuntr - GitHub Repository Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for files containing 'token' anywhere in name
  python githuntr.py -f ".*token.*" -r REPO_URL

  # Search for files ending in .txt
  python githuntr.py -f ".*\\.txt$" -r REPO_URL

  # Search for content containing 'api_key'
  python githuntr.py -c ".*api_key.*" -r REPO_URL

  # Search for exact matches of 'SECRET_TOKEN'
  python githuntr.py -c "^SECRET_TOKEN$" -r REPO_URL

  # Search through commit history
  python githuntr.py -c ".*password.*" --history -r REPO_URL

  # Limit commit history search
  python githuntr.py -c ".*api_key.*" --history --max-commits 100 -r REPO_URL

  # Combine all features
  python githuntr.py -f ".*config.*" -c ".*password.*" -e --history -r REPO_URL
""")
    parser.add_argument('-f', '--filename-regex', help='Regex to match filenames')
    parser.add_argument('-c', '--content-regex', help='Regex to match file content')
    parser.add_argument('-o', '--output-file', help='File to write report json to')
    parser.add_argument('-r', '--repo-url', required=True, help='URL for repo to scan')
    parser.add_argument('-e', '--entropy', action='store_true', 
                       help='Perform Entropy search (slow)')
    parser.add_argument('--history', action='store_true',
                       help='Search through commit history')
    parser.add_argument('--max-commits', type=int,
                       help='Maximum number of commits to search through')
    
    args = parser.parse_args()
    
    # Validate regex patterns
    filename_regex = validate_regex(args.filename_regex, 'filename')
    content_regex = validate_regex(args.content_regex, 'content')
    
    if (args.filename_regex and not filename_regex) or (args.content_regex and not content_regex):
        return 1
    
    try:
        # Check if git is installed
        git.cmd.Git().execute(['git', '--version'])
    except git.exc.GitCommandError:
        print(f"{Fore.RED}Error: Git is not installed or not in PATH. Please install Git first.{Style.RESET_ALL}")
        return 1
    
    try:
        # Initialize and run scanner
        scanner = GitHuntr(args.repo_url, max_commits=args.max_commits)
        results = scanner.scan_repository(
            filename_regex=filename_regex,
            content_regex=content_regex,
            do_entropy=args.entropy,
            search_history=args.history
        )
        
        # Output results
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n{Fore.GREEN}Results written to {args.output_file}{Style.RESET_ALL}")
        else:
            print("\nResults:")
            print(json.dumps(results, indent=2))
            
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main()) 