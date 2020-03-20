"""
ID Utils smart contract for DDXF
"""

from ontology.builtins import state
from ontology.interop.Ontology.Native import Invoke
from ontology.interop.System.App import DynamicAppCall
from ontology.interop.System.Runtime import Notify, CheckWitness
from ontology.interop.System.Storage import GetContext, Get, Put
from ontology.libont import bytearray_reverse
from boa.interop.Ontology.Contract import Migrate
from ontology.interop.Ontology.Runtime import Base58ToAddress

ONTID_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03')
ZERO_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

OWNER = Base58ToAddress("AbtTQJYKfQxq4UdygDsbLVjE8uRrJ2H3tP")

KEY_MARKET_PLACE_ADDRESS = '01'
KEY_DATA_TOKEN_ADDRESS = '02'

ctx = GetContext()


def Main(operation, args):
    if operation == 'reg_ids_with_controller':
        assert (len(args) == 3)
        arr = args[0]
        controller = args[1]
        index = args[2]
        return reg_ids_with_controller(arr, controller, index)
    if operation == 'reg_id_with_controller':
        return reg_id_with_controller(args)
    if operation == 'reg_ids_and_auth_order':
        assert (len(args) == 3)
        arr = args[0]
        controller = args[1]
        group_signer = args[2]
        return reg_ids_and_auth_order(arr, controller, group_signer)
    if operation == 'set_market_place_contract':
        assert (len(args) == 1)
        contract_addr = args[0]
        return set_market_place_contract(contract_addr)
    if operation == 'get_market_place_contract':
        return get_market_place_contract()
    if operation == 'set_data_token_contract':
        assert (len(args) == 1)
        contract_addr = args[0]
        return set_data_token_contract(contract_addr)
    if operation == 'get_data_token_contract':
        return get_data_token_contract()
    if operation == 'take_order_confirm':
        authId = args[0]
        takerReceiveAddress = args[1]
        tokenAmount = args[2]
        OJ = args[3]
        return take_order_confirm(authId, takerReceiveAddress, tokenAmount, OJ)
    if operation == 'add_key':
        assert (len(args) == 2)
        arr = args[0]
        add_pub = args[1]
        return add_key(arr, add_pub)
    if operation == 'remove_key':
        assert (len(args) == 2)
        arr = args[0]
        rm_pub = args[1]
        return remove_key(arr, rm_pub)
    if operation == "upgrade":
        code = args[0]
        name = args[1]
        version = args[2]
        author = args[3]
        email = args[4]
        desc = args[5]
        return upgrade(code, name, version, author, email, desc)
    return False


def upgrade(code, name, version, author, email, desc):
    """
    upgrade current smart contract, it will transfer all the ONT/ONG to the ADMIN wallet address
    :param code: new smart contract avm code(byte code)
    :return:
    """
    assert (CheckWitness(OWNER))
    res = Migrate(code, "", name, version, author, email, desc)
    if not res:
        raise Exception("migrate ddxf market palce smart contract failed")
    Notify(["upgrade success"])
    return True


# arr:[dataId], controller:ontId,index or group
def reg_ids_with_controller(arr, controller, index):
    for item in arr:
        Notify([item, controller, index])
        assert (Invoke(0, ONTID_ADDRESS, "regIDWithController",
                       state(item, controller, index)))  # state(dataId, ontId, index)
    return True


# arr:[[dataId,index, symbol, name, authAmount, price, transferCount, accessCount, expireTime,
# makerTokenHash, makerReceiveAddress, mpReceiveAddress, OJList]], controller:ontId,index or group
def reg_ids_and_auth_order(arr, controller, group_signer):
    assert (len(arr) > 0)
    for item in arr:
        assert (len(item) == 12)
        assert (reg_ids_with_controller([item[0]], controller, group_signer))
        # dataId, index, symbol, name, authAmount, price, transferCount, accessCount, expireTime, makerTokenHash,
        # makerReceiveAddress, mpReceiveAddress, OJList
        assert (DynamicAppCall(bytearray_reverse(get_market_place_contract()), "authOrder",
                               [item[0], group_signer, item[1], item[2], item[3], item[4], item[5], item[6], item[7],
                                item[8],
                                item[9], item[10], item[11]]))
    return True


def set_market_place_contract(contract_addr):
    assert (is_address(contract_addr))
    assert (CheckWitness(OWNER))
    Put(ctx, KEY_MARKET_PLACE_ADDRESS, contract_addr)
    return True


def get_market_place_contract():
    return Get(ctx, KEY_MARKET_PLACE_ADDRESS)


# [[dataId, controller, index]]
def reg_id_with_controller(arr):
    for item in arr:
        assert (len(item) >= 3)
        assert (Invoke(0, ONTID_ADDRESS, "regIDWithController", state(item[0], item[1], item[2])))
    return True


def take_order_confirm(authId, takerReceiveAddress, tokenAmount, OJ):
    # res [orderId, tokenId]
    take_order_res = DynamicAppCall(bytearray_reverse(get_market_place_contract()), "takeOrder",
                                    [authId, takerReceiveAddress, tokenAmount, OJ])
    assert (len(take_order_res) == 2)
    consume_token_res = DynamicAppCall(bytearray_reverse(get_data_token_contract()), "consumeToken",
                                       [take_order_res[1]])
    assert (consume_token_res is True)
    confirm_res = DynamicAppCall(bytearray_reverse(get_market_place_contract()), "confirm", [take_order_res[0]])
    assert (confirm_res is True)
    return True


def set_data_token_contract(contract_addr):
    assert (is_address(contract_addr))
    assert (CheckWitness(OWNER))
    Put(ctx, KEY_DATA_TOKEN_ADDRESS, contract_addr)
    return True


def get_data_token_contract():
    return Get(ctx, KEY_DATA_TOKEN_ADDRESS)


# [[ontid, operatorPub]]
def add_key(arr, add_pub):
    for item in arr:
        assert (len(item) >= 2)
        assert (Invoke(0, ONTID_ADDRESS, "addKey", state(item[0], add_pub, item[1])))
    return True


# [[ontid, operatorPub]]
def remove_key(arr, rm_pub):
    for item in arr:
        assert (len(item) >= 2)
        assert (Invoke(0, ONTID_ADDRESS, "removeKey", state(item[0], rm_pub, item[1])))
    return True


def is_address(address):
    """
    check the address is legal address.
    :param address:
    :return:True or raise exception.
    """
    assert (len(address) == 20 and address != ZERO_ADDRESS)
    return True