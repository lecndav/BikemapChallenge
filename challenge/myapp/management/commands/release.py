import os
import subprocess
import pickle
from enum import Enum
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

STATE_FILE_NAME = 'state.p'
ALLOWED_BRANCH_NAMES = ['feature', 'bug']


class BranchState(Enum):
    TO_BE_TESTED = 1
    APPROVED = 2
    CONFLICTING = 3
    NOT_TRACKABLE = 4
    INIT = 5


class Branch():

    name = ""
    state = BranchState.NOT_TRACKABLE

    def __init__(self, name):
        self.name = name
        self.state = BranchState.INIT


def saveState(state):
    pickle.dump(state, open(STATE_FILE_NAME, "wb"))


def loadState():
    # state: version, branches, branchnames
    stateFile = Path(STATE_FILE_NAME)
    if stateFile.is_file():
        return pickle.load(open(STATE_FILE_NAME, "rb"))
    else:
        return {}


def fetchAll():
    os.system('git fetch origin')


def getRemoteBranches():
    fetchAll()
    result = subprocess.run(['git', 'branch', '-r'], stdout=subprocess.PIPE)
    out = result.stdout.decode('utf-8')
    rows = out.split('\n')
    branches = map(lambda x: '/'.join(x.strip().split('/')[1:]), rows)

    return list(branches)


def mergeBranch(branch):
    # TODO: merge branch into test
    return True


def createBranch(name):
    os.system('git checkout develop')
    os.system('git checkout -b %s' % name)
    return True


def makeMessages():
    # TODO: makemessages
    return True


def mergeBranchesIntoRelease(branches):
    for b in branches:
        if b.state == BranchState.APPROVED:
            mergeBranch(b.name)


class Command(BaseCommand):
    help = 'Release Software'

    def add_arguments(self, parser):
        # release branch
        parser.add_argument('release', type=str)

        # add branches to release
        parser.add_argument('--add', nargs='+', type=str)

        # approve feature branch
        parser.add_argument('--approve', type=str)

        # to be tested branch
        parser.add_argument('--tbt', type=str)

        # create release branch
        parser.add_argument('--finish', action='store_true')

    def handle(self, *args, **options):
        state = loadState()
        # TODO: add checks
        releaseB = options['release']
        version = releaseB.split('/')[1]
        testB = 'test/%s' % version

        if not bool(state):
            # new workflow
            state['version'] = version
            state['branches'] = []
            state['branchNames'] = []
            if not createBranch(testB):
                raise CommandError('Could not create test branch')
            self.stdout.write("Created test branch %s" % testB)

        bNames = getRemoteBranches()

        if options['add']:
            for b in options['add']:
                if b not in bNames:
                    self.stdout.write("Could not find remote to %s! Skipping" %
                                      b)
                    continue

                if b in state['branchNames']:
                    self.stdout.write("Branch %s already included! Skipping" %
                                      b)
                    continue

                # check branch name format
                nameParts = b.split('/')
                if len(nameParts) > 1:
                    if nameParts[0] not in ALLOWED_BRANCH_NAMES:
                        self.stdout.write("Skipping %s" % b)
                else:
                    self.stdout.write("Skipping %s" % b)

                branch = Branch(b)
                if mergeBranch(b):
                    # TODO: check migration
                    state['branches'].append(branch)
                    state['branchNames'].append(b)
                else:
                    raise CommandError(
                        'Could merge branch %s, resolve conflict' % b)

                # saveState(state)

        if options['approve']:
            branch = options['approve']
            c = False
            for b in state['branches']:
                if branch == b.name:
                    b.state = BranchState.APPROVED
                    c = True
                    break
            if c:
                self.stdout.write("Approved %s" % branch)

        if options['tbt']:
            branch = options['tbt']
            c = False
            for b in state['branches']:
                if branch == b.name:
                    b.state = BranchState.TO_BE_TESTED
                    c = True
                    break
            if c:
                self.stdout.write("Set branch %s to be tested" % branch)

        if options['finish']:
            # checkout test branch
            makeMessages()
            createBranch(releaseB)
            mergeBranchesIntoRelease(state['branches'])
            # push branch