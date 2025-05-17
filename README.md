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
python githuntr.py [-h] [-f REGEX] [-c REGEX] [-o FILE] -r REPO_URL [-e] [-H] [-m MAX]

Required Arguments:
  -r, --repo-url        URL for repo to scan

Search Options:
  -f, --filename-regex  Regex to match filenames
  -c, --content-regex   Regex to match file content
  -e, --entropy        Perform Entropy search (slow)
  -H, --history        Search through commit history
  -m, --max-commits    Maximum number of commits to search through

Output Options:
  -o, --output-file    File to write report json to
  -h, --help          Show this help message and exit
```

## Examples

```bash
# Basic search in current state (short form)
python githuntr.py -f ".*token.*" -r git@github.com:username/repo.git

# Search in commit history for passwords (short form)
python githuntr.py -c ".*password.*" -H -r git@github.com:username/repo.git

# Limit history search to last 100 commits (short form)
python githuntr.py -c ".*api_key.*" -H -m 100 -r git@github.com:username/repo.git

# Full scan with all features (short form)
python githuntr.py -f ".*config.*" -c ".*password.*" -e -H -o report.json -r git@github.com:username/repo.git

# Same command with long form options
python githuntr.py --filename-regex ".*config.*" --content-regex ".*password.*" \
                  --entropy --history --output-file report.json --repo-url git@github.com:username/repo.git
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
