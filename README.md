![gitHuntr](banner.png)

# GitHuntr

Multi-platform GitHub search tool written in Python.

Find stuff in GitHub repos and all your branches:

* Search filenames using regex
* Search in file contents using regex
* Entropy search - Similar to TruffleHog

## Installation

You can install GitHuntr using either pip or conda.

### Using pip (Recommended)

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Using conda (Alternative)

1. Make sure you have [Conda](https://docs.conda.io/en/latest/) installed
2. Clone this repository
3. Create the conda environment:
```bash
conda env create -f environment.yml
```
4. Activate the environment:
```bash
conda activate githuntr
```

## Usage

```bash
python githuntr.py [-h] [-f FILENAME_REGEX] [-c CONTENT_REGEX] [-o OUTPUT_FILE] [-r REPO_URL] [-e]

options:
  -h, --help            Show this help message and exit
  -f FILENAME_REGEX     Regex to match filenames
  -c CONTENT_REGEX     Regex to match file content
  -o OUTPUT_FILE        File to write report json to
  -r REPO_URL          URL for repo to scan
  -e                    Perform Entropy search (slow)
  --history            Search through commit history
  --max-commits MAX    Maximum number of commits to search through
```

## Example

```bash
# Search for files containing 'token' anywhere in name
python githuntr.py -f ".*token.*" -r git@github.com:username/repo.git

# Search for files ending in .txt
python githuntr.py -f ".*\.txt$" -r git@github.com:username/repo.git

# Search for content containing 'api_key'
python githuntr.py -c ".*api_key.*" -r git@github.com:username/repo.git

# Search for exact matches of 'SECRET_TOKEN'
python githuntr.py -c "^SECRET_TOKEN$" -r git@github.com:username/repo.git

# Combine filename and content search with entropy scan
python githuntr.py -f ".*config.*" -c ".*password.*" -e -o report.json -r git@github.com:username/repo.git

# Search in commit history for passwords
python githuntr.py -c ".*password.*" --history -r git@github.com:username/repo.git

# Limit history search to last 100 commits
python githuntr.py -c ".*api_key.*" --history --max-commits 100 -r git@github.com:username/repo.git

# Full scan: files, content, entropy, and history
python githuntr.py -f ".*config.*" -c ".*password.*" -e --history -o report.json -r git@github.com:username/repo.git
```

### Regex Pattern Tips

- Use `.*pattern.*` to match 'pattern' anywhere in the text
- Use `^pattern$` to match exact text
- Use `.*\.extension$` to match file extensions
- Use `pattern1|pattern2` to match multiple patterns
- Escape special characters with backslash: `\.`, `*`, `$`

## Requirements

- Python 3.6 or higher
- Git command-line tool installed and accessible in PATH
- GitHub authentication set up in your terminal (SSH key or HTTPS credentials)

### GitHub Authentication

GitHuntr uses your local Git credentials to access repositories. Make sure you have:

1. **SSH Authentication** (Recommended):
   - Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
   - Add to GitHub: Copy key from `~/.ssh/id_ed25519.pub` to GitHub Settings → SSH Keys
   - Use SSH URLs: `git@github.com:username/repo.git`

2. **HTTPS Authentication**:
   - Configure Git credentials: `git config --global credential.helper store`
   - Use HTTPS URLs: `https://github.com/username/repo.git`

3. **GitHub CLI**:
   - Install GitHub CLI: [cli.github.com](https://cli.github.com)
   - Authenticate: `gh auth login`

## Platforms
* Windows
* macOS
* Linux

## Version
1.0.0

## License
Apache 2.0

## Author
Original Pascal version by Marcus Fernström
Python version by Nestor Torres
