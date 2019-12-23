from ontology.interop.System.Action import RegisterAction
from ontology.interop.Ontology.Runtime import Base58ToAddress
from ontology.interop.System.Storage import Get, GetContext, Put
from ontology.builtins import sha256, concat
from ontology.interop.System.Runtime import Serialize, Deserialize, Log, CheckWitness

# vote status
STATUS_NOT_FOUND = 'not found'
STATUS_VOTING = 'voting'
STATUS_END = 'end'

PRE_TOPIC = '01'
PRE_MIN_AMOUNT = '02'
PRE_VOTER = '03'
PRE_VOTED = '04'

KEY_ALL_TOPIC = 'all_topic'

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
    if operation == 'getVoters':
        Require(len(args) == 1)
        hash = args[0]
        return getVoters(hash)
    if operation == 'voteTopic':
        Require(len(args) == 2)
        hash = args[0]
        voter = args[1]
        return voteTopic(hash, voter)
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
    key = getKey(PRE_TOPIC, hash)
    data = Get(ctx, key)
    if data:
        return False
    topicInfo = [topic, STATUS_VOTING, 0]
    Put(ctx, key, Serialize(topicInfo))
    bs = Get(ctx, KEY_ALL_TOPIC)
    if bs:
        topics = Deserialize(bs)
    else:
        topics = []
    topics.append(topic)
    bs = Serialize(topics)
    Put(ctx, KEY_ALL_TOPIC, bs)
    CreateTopicEvent(hash, topic)
    return True


# def setMinAmountForVote(hash,value):
#     RequireWitness(ADMIN)
#     Require(value > 0)
#     key = getKey(PRE_MIN_AMOUNT, hash)
#     Put(key,value)

def setVoterForTopic(hash, voters):
    RequireWitness(ADMIN)
    key = getKey(PRE_VOTER, hash)
    info = Get(ctx, key)
    if info:
        return False
    Put(ctx, key, Serialize(voters))
    return True


# ****all user can invoke method ***********
def listTopics():
    bs = Get(ctx, KEY_ALL_TOPIC)
    topics = Deserialize(bs)
    return topics


def getTopic(hash):
    key = getKey(PRE_TOPIC, hash)
    info = Get(ctx, key)
    if info == None:
        return []
    return Deserialize(info)


def getVoters(hash):
    key = getKey(PRE_VOTER, hash)
    info = Get(ctx, key)
    if info == None:
        return False
    voters = Deserialize(info)
    return voters


def voteTopic(hash, voter):
    RequireWitness(voter)
    Require(isValidVoter(hash, voter))
    Require(hasVoted(hash, voter) == False)
    topicInfo = getTopic(hash)
    if len(topicInfo) < 3:
        return False
    if topicInfo[1] != STATUS_VOTING:
        return False
    topicInfo[2] += 1
    voters = getVoters(hash)
    if topicInfo[2] > len(voters) / 2:
        topicInfo[1] = STATUS_END
    keyTopic = getKey(PRE_TOPIC, hash)
    Put(ctx, keyTopic, Serialize(topicInfo))
    updateVotedAddress(voter, hash)
    VoteTopicEvent(hash, voter)
    return True


def getTopicStatus(hash):
    key = getKey(PRE_TOPIC, hash)
    info = Get(ctx, key)
    if info == None:
        return STATUS_NOT_FOUND
    topicInfo = Deserialize(info)
    return topicInfo[1]


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