from enum import Enum
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
import pickle

STATE_FILE_NAME = 'state.p'
ALLOWED_BRANCH_NAMES = ['feature', 'bug']


class BranchState(Enum):
    TO_BE_TESTED = 1
    APPROVED = 2
    CONFLICTING = 3
    NOT_TRACKABLE = 4


class Branch():

    name = ""
    state = BranchState.NOT_TRACKABLE

    def __init__(self, name):
        self.name = name
        nameParts = self.name.split('/')
        if len(nameParts) > 1:
            if nameParts[0] in ALLOWED_BRANCH_NAMES:
                self.state = BranchState.TO_BE_TESTED


def saveState(state):
    pickle.dump(state, open(STATE_FILE_NAME, "wb"))


def loadState():
    # load state from pickle file
    stateFile = Path(STATE_FILE_NAME)
    if stateFile.is_file():
        return pickle.load(open(STATE_FILE_NAME, "rb"))
    else:
        return {}


def getRemoteBranches():
    # from oririn

    # workaround
    branches = [
        'main', 'release/1.1.1', 'feature/added-sum', 'feature/added-sub',
        'feature/added-multiplay', 'bug/added-diff', 'some/thing'
    ]
    return branches


class Command(BaseCommand):
    help = 'Release Software'

    def add_arguments(self, parser):
        # start workflow with branch names
        parser.add_argument('--start', nargs='+', type=str)

        # approve feature branch
        parser.add_argument('--approved', type=str)

        # to be tested branch
        parser.add_argument('--tbt', type=str)

        # create release branch
        parser.add_argument('--release', type=bool)

    def handle(self, *args, **options):
        state = {}
        if options['start']:
            state = loadState()
            if bool(state):
                raise CommandError(
                    'Release already with version %s already started!' %
                    state['version'])

            bNames = getRemoteBranches()
            branches = []
            for b in options['start']:
                if b not in bNames:
                    self.stdout.write("Could not find remote to %s! Skipping" %
                                      b)
                    continue
                branch = Branch(b)
                if branch.state == BranchState.TO_BE_TESTED:
                    branches.append(branch)
                else:
                    self.stdout.write("Skipping %s" % b)

            if len(branches) == 0:
                self.stdout.write("Nothing to do!")
                exit(0)

            
