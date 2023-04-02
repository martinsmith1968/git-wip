import sys
import contextlib
import os
import glob
import git
import re
from argparse import ArgumentParser
from rich.progress import Progress


# Useful Links:
#  https://stackoverflow.com/questions/43037807/find-out-if-changes-were-pushed-to-origin-in-gitpython


DefaultMainBranches = [ "main", "master", "wikiMaster", "primary" ]
DefaultRemotes      = [ "origin", "azure", "devops" ]

AllRepos                = [ ]
NonGitDirectories       = [ ]
ReposInError            = [ ]
ReposNotOnPrimaryBranch = [ ]
ReposAhead              = [ ]
ReposBehind             = [ ]
ReposWithUncommitted    = [ ]
ReposPulled             = [ ]
ReposPrinted            = [ ]


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def indentText(count, *text):
    return str('  ' * count) + ' '.join(str(x) for x in text)


class MyParser(ArgumentParser):
    def error(self, message):
        self.print_help()
        #sys.stderr.write('\nERROR: %s\n' % message)
        eprint('\nERROR: %s\n' % message)
        sys.exit(2)


class MyProgressPrinter(git.RemoteProgress):

    def __init__(self):
        self.progress = Progress() #transient=True)
        self.downloadTask = self.progress.add_task("[yellow]Pulling...", total=100)
        self.updatesMade = 0
        super().__init__()

    def update(self, op_code, cur_count, max_count=None, message=""):
        percent_complete = cur_count / (max_count or 100.0)
        self.progress.update(self.downloadTask, completed=percent_complete)


@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def isGitRepo(dir):
    try:
        git.Repo(dir)
    except:
        return False
    else:
        return True


def getRepoName(repo):
    path = repo.working_dir
    return os.path.basename(path)


def doesGitBranchExist(repo, branchName):
    try:
        repo.heads[branchName]
    except:
        return False
    else:
        return True
    

def doesGitRemoteExist(repo, remoteName):
    try:
        repo.remotes[remoteName]
    except:
        return False
    else:
        return True
    

def isGitRemoteValid(repo, remoteName):
    if not doesGitRemoteExist(repo, remoteName):
        return False
    
    remote = repo.remotes[remoteName]

    return remote.exists()


def getGitPrimaryBranch(repo):
    for mainBranchName in DefaultMainBranches:
        if doesGitBranchExist(repo, mainBranchName):
            return repo.heads[mainBranchName]

    return None


def isGitBranchPrimary(branchName):
    for mainBranchName in DefaultMainBranches:
        if branchName == mainBranchName:
            return True

    return False


def getGitPrimaryRemote(repo):
    for remoteName in DefaultRemotes:
        if doesGitRemoteExist(repo, remoteName):
            return repo.remotes[remoteName]

    return None


def processAllReposUnderDirFromDir(dir, args, indent = 0):
    with pushd(args.directory):
        container_dirs = glob.glob(args.directory_wildcard)
        print(indentText(indent, "Found", len(container_dirs), "container directories"))

        index = 0
        for container_dir in container_dirs:
            if os.path.isdir(container_dir):
                print(indentText(indent, "Container:", container_dir))
                index += 1
                processAllReposUnderDir(container_dir, args, indent + 1)


def processAllReposUnderDir(dir, args, indent = 0):
    with pushd(dir):
        sub_dirs = glob.glob(args.directory_wildcard)
        print(indentText(indent, "Found", len(sub_dirs), "directories"))

        index = 0
        for sub_dir in sub_dirs:
            if os.path.isdir(sub_dir):
                index += 1
                processDir(sub_dir, args, index, indent + 1)


def processDir(dir, args, index = 0, indent = 1):   # TODO
    with pushd(dir):
        if not isGitRepo("."):
            NonGitDirectories.append(dir)
            return
        
        repo_identifier = ""
        output_lines = [ ]

        if index > 0 and args.showRepoIndex:
            repo_identifier = indentText(indent, f"{index}: {dir}")
        else:
            repo_identifier = indentText(indent, str(dir))

        # Access repo
        repo = git.Repo(".")
        AllRepos.append(repo)

        # Determine current state
        primaryBranch = getGitPrimaryBranch(repo)
        currentBranch = repo.head.ref.name
        primaryRemote = getGitPrimaryRemote(repo)

        isOnPrimaryBranch = isGitBranchPrimary(currentBranch)
        ahead = 0
        behind = 0

        repo_status = repo.git.status(porcelain="v2", branch=True)
        ahead_behind_match = re.search(r"#\sbranch\.ab\s\+(\d+)\s-(\d+)", repo_status)

        if ahead_behind_match:
            ahead = int(ahead_behind_match.group(1))
            behind = int(ahead_behind_match.group(2))

        if ahead:
            ReposAhead.append(repo)
        if behind:
            ReposAhead.append(repo)

        # Show Branch ?
        showBranch = (args.showOnPrimary and isOnPrimaryBranch) or (args.showOnNonPrimary and not isOnPrimaryBranch)
        if showBranch:
            output_lines.append(indentText(indent + 1, f"Branch: {currentBranch}"))

        # Show Out of Date (Ahead / Behind) ?
        if args.showOutOfDate:
            if ahead:
                output_lines.append(indentText(indent + 1, f"Ahead by {ahead} commits"))
            if behind:
                output_lines.append(indentText(indent + 1, ), f"Behind by {ahead} commits")

        # Show Untracked / uncomitted
        if (args.showUncommittedFiles):
            if repo.untracked_files:
                ReposWithUncommitted.append(repo)
                for file in repo.untracked_files:
                    output_lines.append(indentText(indent + 1, f"Untracked: {file}"))

        # Pull from remote ?
        pulling = False

        if (args.pullOnPrimary or args.pullOnNonPrimary) and behind:
            remote = getGitPrimaryRemote(repo)
            if remote:
                if not isGitRemoteValid(repo, remote.name):
                    output_lines.append(indentText(indent + 1, "ERROR: Remote not accessible"))
                else:
                    primaryBranchName = getGitPrimaryBranch(repo)
                    if (primaryBranchName):
                        primaryBranchName = primaryBranchName.name

                if args.pullOnPrimary and repo.head.ref.name == primaryBranchName:
                    pulling = True

                if args.pullOnNonPrimary and repo.head.ref.name != primaryBranchName:
                    pulling = True

        if pulling:            
            output_lines.append(indentText(indent + 1, "Pulling..."))

        # If there is output for this repo, then print it now
        if output_lines:
            ReposPrinted.append(repo)
            print (repo_identifier)
            for line in output_lines:
                print (line)

        # Pull commits from remote
        if pulling:
            try:
                remote.pull(progress=MyProgressPrinter())
            except Exception as e:
                output_lines.append(indentText(indent + 1, f"ERROR: {e}"))
                ReposInError.append(repo)


def _main():
    parser = MyParser(description="Analyse a GIT repo")
    parser.add_argument("-v", "--version", action='version', version='%(prog)s 1.0')
    parser.add_argument("-d", "--directory", dest="directory", required=True, help="The directory to analyze")
    parser.add_argument("-m", "--mode", dest="mode", default='repo', choices=['repo', 'dir_of_repos', 'dir_of_dir_of_repos', 'tree_search'], help="The processing mode")
    parser.add_argument("-w", "--directory-wildcard", dest="directory_wildcard", default="*", help="The wildcard directory pattern to use for repo directory selection")
    parser.add_argument("-b", "--primary-branches", dest="primary_branch", help="The branch name to use as primary")
    parser.add_argument("-o", "--default-origins", dest="default_origins", help="The origin names to use by default")
    parser.add_argument("-n", "--notes-files", dest="notes_file", metavar="FILE", help="The file containing notes for each repo")

    group = parser.add_argument_group('Processing Options')
    group.add_argument("-sri",  "--show-repo-index", dest="showRepoIndex", default=False, action='store_true', help="Show index number of Repo")
    group.add_argument("-sop",  "--show-on-primary-branch", dest="showOnPrimary", default=False, action='store_true', help="Show details if on primary branch")             # TODO
    group.add_argument("-sonp", "--show-on-non-primary-branch", dest="showOnNonPrimary", default=False, action='store_true', help="Show details if on non-primary branch")  # TODO
    group.add_argument("-sood", "--show-out-of-date", dest="showOutOfDate", default=False, action='store_true', help="Show Out of Date commits")
    group.add_argument("-pop",  "--pull-on-primary-branch", dest="pullOnPrimary", default=False, action='store_true', help="Pull if on primary branch")
    group.add_argument("-ponp", "--pull-on-non-primary-branch", dest="pullOnNonPrimary", default=False, action='store_true', help="Pull if on non-primary branch")
    group.add_argument("-suc",  "--show-uncommitted-files", dest="showUncommittedFiles", default=False, action='store_true', help="Show any uncommitted files (WIP)")
    group.add_argument("-sn",   "--show-notes", dest="showNotes", default='always', choices=['no', 'primary', 'always'], help="Show any supporting notes")
    group.add_argument("-ns",   "--no-summary", dest="showSummary", default=True, action='store_false', help="Show aa summary of processing")

    # Parse
    args = parser.parse_args()

    # Process
    match args.mode:
        case 'repo':
            processDir(args.directory, args)
        case 'dir_of_repos':
            processAllReposUnderDir(args.directory, args)
        case 'dir_of_dir_of_repos':
            processAllReposUnderDirFromDir(args.directory, args)
        case _:
            raise Exception(f"Unexpected or currently unsupported 'mode': {args.mode}")
        

    if args.showSummary:
        print ("")
        print ("Summary")
        print ("=======")
        print ("Total Repos :", len(AllRepos))

        if ReposPrinted:
            print ("")
            print ("Repos printed :", len(ReposPrinted))

        if NonGitDirectories:
            print ("")
            print ("Non-git Repos :", len(NonGitDirectories))
            for dir in NonGitDirectories:
                print ("  ", dir)

        if ReposInError:
            print ("")
            print ("Repos in Error :", len(ReposInError))
            for repo in ReposInError:
                print (indentText(1, getRepoName(repo)))

        if ReposWithUncommitted:
            print ("")
            print ("Repos with uncommitted files :", len(ReposWithUncommitted))
            for repo in ReposWithUncommitted:
                print (indentText(1, getRepoName(repo)))

        if ReposAhead:
            print ("")
            print ("Repos ahead of remote :", len(ReposAhead))
            for repo in ReposAhead:
                print (indentText(1, getRepoName(repo)))

        if ReposBehind:
            print ("")
            print ("Repos behind remote :", len(ReposAhead))
            for repo in ReposBehind:
                print (indentText(1, getRepoName(repo)))

        if ReposNotOnPrimaryBranch:
            print ("")
            print ("Repos not on Primary Branch :", len(ReposNotOnPrimaryBranch))
            for repo in ReposNotOnPrimaryBranch:
                print (indentText(1, getRepoName(repo)))

        if ReposPulled:
            print ("")
            print ("Repos pulled :", len(ReposPulled))
            for repo in ReposPulled:
                print (indentText(1, getRepoName(repo)))






if __name__ == '__main__':
    _main()
