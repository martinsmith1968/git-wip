# git-wip

Analyse one or more local GIT repositories and report on state

See [ToDo](TODO.md)

## Usage

```text
usage: gitwip.py [-h] [-v] -d DIRECTORY [-m {repo,dir_of_repos,dir_of_dir_of_repos,tree}] [-w DIRECTORY_WILDCARD] [-b PRIMARY_BRANCH] [-o DEFAULT_ORIGINS] [-n FILE] [-sri] [-sop] [-sonp] [-sood] [-pop] [-ponp] [-suc] [-sn {no,primary,always}] [-ns]

Analyse a GIT repo

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d DIRECTORY, --directory DIRECTORY
                        The directory to analyze
  -m {repo,dir_of_repos,dir_of_dir_of_repos,tree}, --mode {repo,dir_of_repos,dir_of_dir_of_repos,tree}
                        The processing mode
  -w DIRECTORY_WILDCARD, --directory-wildcard DIRECTORY_WILDCARD
                        The wildcard directory pattern to use for repo directory selection
  -b PRIMARY_BRANCH, --primary-branches PRIMARY_BRANCH
                        The branch name to use as primary
  -o DEFAULT_ORIGINS, --default-origins DEFAULT_ORIGINS
                        The origin names to use by default
  -n FILE, --notes-files FILE
                        The file containing notes for each repo

Processing Options:
  -sri, --show-repo-index
                        Show index number of Repo
  -sop, --show-on-primary-branch
                        Show details if on primary branch
  -sonp, --show-on-non-primary-branch
                        Show details if on non-primary branch
  -sood, --show-out-of-date
                        Show Out of Date commits
  -pop, --pull-on-primary-branch
                        Pull if on primary branch
  -ponp, --pull-on-non-primary-branch
                        Pull if on non-primary branch
  -suc, --show-uncommitted-files
                        Show any uncommitted files (WIP)
  -sn {no,primary,always}, --show-notes {no,primary,always}
                        Show any supporting notes
  -ns, --no-summary     Show aa summary of processing
```
