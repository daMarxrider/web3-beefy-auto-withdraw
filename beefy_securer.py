from web3 import Web3
import json
import requests
import time
from joblib import *
import os

path = os.path.abspath(os.path.dirname(__file__))
with open(f'{path}{os.sep}network_config.json', 'r') as file:
    networks = json.loads(''.join(file.readlines()))


def check_abi_for_bad_formatting(abi):
    try:
        tmp_json = json.loads(abi)
        if 'abi' in tmp_json:
            abi = tmp_json['abi']
    except:
        pass
    return abi


def get_contract_abi(network, address):
    contract_dir = f'{path}{os.sep}networks{os.sep}{network["chainName"]}'
    # obligatory reminder:
    # python has extremely optimized try-catch-blocks and
    # is faster than if os.exists
    try:
        os.makedirs(contract_dir, exist_ok=True)
        with open(f'{contract_dir}{os.sep}abi_{address}', 'r') as file:
            abi = ''.join(file.readlines())
    except FileNotFoundError:
        abi = requests.get(network['abiUrl'].replace('$address',
                                                     address)).content.decode()
        with open(f'{contract_dir}{os.sep}abi_{address}', 'w') as file:
            file.write(abi)
    abi = check_abi_for_bad_formatting(abi)
    return abi


# https://github.com/beefyfinance/beefy-app/blob/master/src/features/configure/vault/bsc_pools.js
# https://github.com/beefyfinance/beefy-app/blob/master/src/features/configure/abi.js
# https://github.com/beefyfinance/beefy-app/blob/master/src/common/networkSetup.js


def withdraw_from_beefy(w3, network, token):
    token_contract = w3.eth.contract(address=token['address'],
                                     abi=get_contract_abi(
                                         network, token['address']))
    nonce = w3.eth.get_transaction_count(token['yourPubKey'])
    withdraw_function = getattr(token_contract.functions, token['method'])

    unsigned_tx = withdraw_function().buildTransaction({
        'from':token['yourPubKey'],
        'chainId': token['chainId'],
        'nonce': nonce
    })
    print(unsigned_tx)
    signed_tx = w3.eth.account.sign_transaction(unsigned_tx,
                                                private_key=token['privateKey'])
    w3.eth.send_raw_transaction(signed_tx)


def check_blocks_for_event(w3, contract, tokens, network, from_block, to_block):
    print(f'checking {from_block}-{to_block} for chain {network["chainId"]}')
    event = getattr(contract.events, network['timelockMethod'])
    event_filter = event.createFilter(fromBlock=from_block, toBlock=to_block)
    try:
        for Pair in event_filter.get_new_entries():
            print(Pair)
            # print(Pair.hex())
            try:
                print(Pair['args'])
                print(Pair['args']['target'].lower())
                target = Pair['args']['target'].lower()
                for token in tokens:
                    if token['address'].lower() == target:
                        withdraw_from_beefy(w3, network, token)
            except TypeError:
                print('this sould be filtered')
                print(Pair)
            except Exception as ex:
                print(ex)
    except Exception as ex:
        print(ex)
        # print(dir(Pair))
    network['last_height'] = to_block - 1
    print(f"last height: {network['last_height']}")
    time.sleep(60 / len(networks))


def main():
    global networks
    watched_tokens = []
    with open(f'{path}{os.sep}config.json', 'r') as file:
        watched_tokens = json.loads(''.join(file.readlines()))
    # print(watched_tokens)
    while True:
        for network in networks:
            try:
                tokens_on_current_chain = [
                    token for token in watched_tokens
                    if token['chainId'] == network['chainId']
                ]
                if 'instance' not in network:
                    w3 = Web3(Web3.HTTPProvider(network['rpcUrls'][0]))
                    network['instance'] = w3
                else:
                    w3 = network['instance']
                timelock_abi = get_contract_abi(network, network['timelockAddress'])
                timelock_contract = w3.eth.contract(
                    address=network['timelockAddress'], abi=timelock_abi)
                latest_block = w3.eth.block_number
                print("latest block: %s" % latest_block)
                from_block = network['last_height'] if 'last_height' in network \
                    else latest_block - network['timelockBlocks']
                if latest_block < from_block:
                    print("possible chain reorg?")
                    from_block = latest_block
                print("from block: %s" % from_block)
                to_block = latest_block if from_block + network[
                    'queryBlockAmount'] > latest_block else from_block + network[
                        'queryBlockAmount']
                print("to block: %s" % to_block)
                check_blocks_for_event(w3, timelock_contract,
                                       tokens_on_current_chain, network, from_block,
                                       to_block)
            except Exception as e:
                print(e)
            finally:
                print('-'*80)
        # time.sleep(300)


if __name__ == '__main__':
    main()
