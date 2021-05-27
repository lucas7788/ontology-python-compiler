OntCversion = '2.0.0'

from ontology.interop.System.Storage import GetContext
from ontology.interop.Ontology.Eth import InvokeEthContract

ctx = GetContext()

def Main(operation, args):
    if operation == 'invokeEthContract':
        return callEth(args[0], args[1], args[2])
    return False


def callEth(contractAddress, method, args):
    return InvokeEthContract(1, contractAddress, method, args)
