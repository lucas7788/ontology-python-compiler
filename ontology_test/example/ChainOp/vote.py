from ontology.interop.System.Action import RegisterAction
from ontology.interop.Ontology.Runtime import Base58ToAddress
from ontology.interop.System.Storage import Get, GetContext, Put
from ontology.builtins import sha256, concat
from ontology.interop.System.Runtime import Serialize, Deserialize, Log, CheckWitness

# vote status
STATUS_NOT_FOUND = 'not found'
STATUS_VOTING = 'voting'
STATUS_END = 'end'

# pre + hash -> topic
PRE_TOPIC = '01'
# topic_info + hash -> topicInfo:[status, up, down,voters]
PRE_TOPIC_INFO = '02'
# pre + hash -> voted address
PRE_VOTED = '03'

# key -> all topic hash
KEY_ALL_TOPIC_HASH = 'all_hash'

ctx = GetContext()
ADMIN = Base58ToAddress("AbtTQJYKfQxq4UdygDsbLVjE8uRrJ2H3tP")

CreateTopicEvent = RegisterAction("createTopic", "hash", "topic")
VoteTopicEvent = RegisterAction("voteTopic", "hash", "voter")


def Main(operation, args):
    """
    only admin can invoke
    """
    if operation == 'createTopic':
        Require(len(args) == 1)
        topic = args[0]
        return createTopic(topic)
    if operation == 'setVoterForTopic':
        Require(len(args) == 2)
        hash = args[0]
        voters = args[1]
        return setVoterForTopic(hash, voters)
    # all user can invoke
    if operation == 'listTopics':
        Require(len(args) == 0)
        return listTopics()
    if operation == 'getTopic':
        Require(len(args) == 1)
        hash = args[0]
        return getTopic(hash)
    if operation == 'getTopicInfo':
        Require(len(args) == 1)
        hash = args[0]
        return getTopicInfo(hash)
    if operation == 'getVoters':
        Require(len(args) == 1)
        hash = args[0]
        return getVoters(hash)
    if operation == 'voteTopic':
        Require(len(args) == 3)
        hash = args[0]
        voter = args[1]
        upOrDown = args[2]
        return voteTopic(hash, voter, upOrDown)
    if operation == 'getTopicStatus':
        Require(len(args) == 1)
        hash = args[0]
        return getTopicStatus(hash)
    return False


# ****only admin can invoke*********
# create a voting topic
def createTopic(topic):
    RequireWitness(ADMIN)
    hash = sha256(topic)
    keyTopic = getKey(PRE_TOPIC, hash)
    data = Get(ctx, keyTopic)
    if data:
        return False
    Put(ctx, keyTopic, topic)
    keyTopicInfo = getKey(PRE_TOPIC_INFO, hash)
    topicInfo = [STATUS_VOTING, 0, 0]  #[status, up amount, down amount, voter address]
    Put(ctx, keyTopicInfo, Serialize(topicInfo))
    hashs = []
    bs = Get(ctx, KEY_ALL_TOPIC_HASH)
    if bs:
        hashs = Deserialize(bs)
    hashs.append(hash)
    Put(ctx, KEY_ALL_TOPIC_HASH, Serialize(hashs))
    CreateTopicEvent(hash, topic)
    return True

def setVoterForTopic(hash, voters):
    RequireWitness(ADMIN)
    key = getKey(PRE_TOPIC_INFO, hash)
    info = Get(ctx, key)
    if info == None:
        return False
    topicInfo = Deserialize(info)
    if len(topicInfo) != 3:
        return False
    else:
        topicInfo.append(voters)
    Put(ctx, key, Serialize(topicInfo))
    return True


# ****all user can invoke method ***********
def listTopics():
    bs = Get(ctx, KEY_ALL_TOPIC_HASH)
    if bs == None:
        return []
    else:
        return Deserialize(bs)


def getTopic(hash):
    key = getKey(PRE_TOPIC, hash)
    return Get(ctx, key)

def getTopicInfo(hash):
    key = getKey(PRE_TOPIC_INFO, hash)
    info = Get(ctx, key)
    if info == None:
        return []
    return Deserialize(info)

def getVoters(hash):
    key = getKey(PRE_TOPIC_INFO, hash)
    info = Get(ctx, key)
    if info == None:
        return []
    topicInfo = Deserialize(info)
    if len(topicInfo) < 4:
        return []
    else:
        return topicInfo[3]


def voteTopic(hash, voter, upOrDown):
    RequireWitness(voter)
    Require(isValidVoter(hash, voter))
    Require(hasVoted(hash, voter) == False)
    topicInfo = getTopicInfo(hash)
    if len(topicInfo) < 4:
        return False
    if topicInfo[0] != STATUS_VOTING:
        return False
    if upOrDown:
        topicInfo[1] += 1
    else:
        topicInfo[2] += 1
    voters = getVoters(hash)
    if topicInfo[1] > len(voters) / 2 | topicInfo[2] > len(voters) / 2:
        topicInfo[0] = STATUS_END
    keyTopicInfo = getKey(PRE_TOPIC_INFO, hash)
    Put(ctx, keyTopicInfo, Serialize(topicInfo))
    updateVotedAddress(voter, hash)
    VoteTopicEvent(hash, voter)
    return True


def getTopicStatus(hash):
    key = getKey(PRE_TOPIC_INFO, hash)
    info = Get(ctx, key)
    if info == None:
        return STATUS_NOT_FOUND
    topicInfo = Deserialize(info)
    return topicInfo[0]


def isValidVoter(hash, voter):
    voters = getVoters(hash)
    for addr in voters:
        if addr == voter:
            return True
    return False


def updateVotedAddress(voter, hash):
    key = getKey(PRE_VOTED, hash)
    info = Get(ctx, key)
    votedAddrs = []
    if info != None:
        votedAddrs = Deserialize(info)
    votedAddrs.append(voter)
    Put(ctx, key, Serialize(votedAddrs))


def hasVoted(hash, voter):
    key = getKey(PRE_VOTED, hash)
    info = Get(ctx, key)
    if info == None:
        return False
    else:
        voters = Deserialize(info)
        for v in voters:
            if v == voter:
                return True
    return False


def getKey(pre, hash):
    '''
    Gets the storage key for looking up a balance
    :param address:
    '''
    key = concat(pre, hash)  # pylint: disable=E0602
    return key


def RequireWitness(address):
    '''
    Raises an exception if the given address is not a witness.
    :param address: The address to check.
    '''
    Require(CheckWitness(address), "Address is not witness")


def Require(expr, message="There was an error"):
    '''
    Raises an exception if the given expression is false.
    :param expr: The expression to evaluate.
    :param message: The error message to log.
    '''
    if not expr:
        Log(message)
        raise Exception(message)