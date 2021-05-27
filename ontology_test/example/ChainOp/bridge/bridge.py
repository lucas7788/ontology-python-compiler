OntCversion = '2.0.0'

from ontology.builtins import concat
from ontology.interop.System.Action import RegisterAction
from ontology.interop.System.App import DynamicAppCall
from ontology.interop.System.ExecutionEngine import GetExecutingScriptHash
from ontology.interop.System.Runtime import CheckWitness
from ontology.libont import bytearray_reverse
from ontology.interop.System.Storage import GetContext
from ontology.interop.Ontology.Eth import InvokeEthContract


Oep4ToErc20Event = RegisterAction("deposit", "ont_acct", "eth_acct", "amount", "ont_token_address", "eth_token_address")
Erc20ToOep4Event = RegisterAction("withdraw", "eth_acct", "ont_acct", "amount", "ont_token_address",
                                  "eth_token_address")

TRANSFER_ID = bytearray(b'\xa9\x05\x9c\xbb')
TRANSFER_FROM_ID = bytearray(b'\x23\xb8\x72\xdd')

ctx = GetContext()
ethVersion = 1


def Main(operation, args):
    if operation == 'oep4ToErc20':
        assert (len(args) == 5)
        return oep4ToErc20(args[0], args[1], args[2], args[3], args[4])
    if operation == 'erc20ToOep4':
        assert (len(args) == 5)
        return erc20ToOep4(args[0], args[1], args[2], args[3], args[4])
    return False


def oep4ToErc20(ont_acct, eth_acct, amount, ont_token_address, eth_token_address):
    """
    deposit amount of tokens from ontology to ethereum
    :param ont_acct: the ontology account from which the amount of tokens will be transferred
    :param eth_acct: the ethereum account to which the amount of tokens will be transferred
    :param amount: the amount of the tokens to be deposited, >= 0
    :param token_addr: the token address
    :return: True means success, False or raising exception means failure.
    """
    assert (len(ont_acct) == 20)
    assert (len(eth_acct) == 20)
    assert (CheckWitness(ont_acct))
    assert (amount > 0)

    this = GetExecutingScriptHash()
    assert (DynamicAppCall(bytearray_reverse(ont_token_address), "transfer", [ont_acct, this, amount]))
    transferData = genEthTransferData(eth_acct, amount)
    assert (InvokeEthContract(ethVersion, eth_token_address, transferData))
    Oep4ToErc20Event(ont_acct, eth_acct, amount, ont_token_address, eth_token_address)
    return True


def erc20ToOep4(eth_acct, ont_acct, amount, ont_token_address, eth_token_address):
    """
    withdraw amount of tokens from ethereum to ontology
    :param ont_addr: the ontology account to which the amount of tokens will be transferred
    :param eth_acct: the ethereum account from which the amount of tokens will be transferred
    :param amount: the amount of the tokens to be withdrawed, >= 0
    :return: True means success, False or raising exception means failure.
    """
    assert (len(ont_acct) == 20)
    assert (len(eth_acct) == 20)
    assert (CheckWitness(eth_acct))
    assert (amount > 0)

    this = GetExecutingScriptHash()
    tranferFromData = genEthTransferFromData(eth_acct, this, amount)
    assert (InvokeEthContract(ethVersion, eth_token_address, tranferFromData))
    assert (DynamicAppCall(bytearray_reverse(ont_token_address), "transfer", [this, ont_acct, amount]))
    Erc20ToOep4Event(eth_acct, ont_acct, amount, ont_token_address, eth_token_address)
    return True


def genEthTransferData(to, amount):
    return concat(concat(TRANSFER_ID, formatAddr(to)), formatAmount(amount))


def genEthTransferFromData(from_acct, to_acct, amount):
    data = concat(TRANSFER_FROM_ID, formatAddr(from_acct))
    data = concat(data, formatAddr(to_acct))
    return concat(data, formatAmount(amount))


def formatAmount(amount):
    data = bytearray(amount)
    prefix = bytearray(b'\x00')
    data_len = len(data)
    assert (data_len <= 32)
    for index in range(32-data_len):
        data = concat(prefix, data)
    return data


def formatAddr(addr):
    assert (len(addr) == 20)
    prefix = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    return concat(prefix, addr)
