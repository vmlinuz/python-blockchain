import functools
import json
import pickle
from collections import OrderedDict

from hash_util import hash_block, hash_string_256

# The reward we give to miners (for creating a new block)
MINING_REWARD = 10

# Initializing our (empty) blockchain list
blockchain = []
# Unhandled transactions
open_transactions = []
# We are the owner of this blockchain node, hence this is our identifier (e.g. for sending coins)
owner = "Gyula"
# Registered participants: Ourself + other people sending/receiving coins
participants = {owner}

blockchain_file_text = "blockchain.txt"
blockchain_file_pickle = "blockchain.pickle"


def init_blockchain():
    """Initialize blockchain list."""
    global blockchain
    global open_transactions
    # Our starting block for the blockchain
    genesis_block = {
        "previous_hash": "",
        "index": 0,
        "transactions": [],
        "proof": 100,
    }
    # Initializing blockchain list with the genesis block
    blockchain = [genesis_block]
    # Cleaning unhandled transactions
    open_transactions = []


def load_data_json():
    """Initializes blockchain + open transactions data from a file."""
    global blockchain
    global open_transactions
    try:
        with open(blockchain_file_text, mode="r") as f:
            file_content = f.readlines()
            orig_blockchain = json.loads(file_content[0][:-1])
            orig_open_transactions = json.loads(file_content[1])
            updated_blockchain = []
            for block in orig_blockchain:
                updated_block = {
                    "previous_hash": block["previous_hash"],
                    "index": block["index"],
                    "proof": block["proof"],
                    "transactions": [
                        OrderedDict(
                            [
                                ("sender", tx["sender"]),
                                ("recipient", tx["recipient"]),
                                ("amount", tx["amount"]),
                            ]
                        )
                        for tx in block["transactions"]
                    ],
                }
                updated_blockchain.append(updated_block)
            blockchain = updated_blockchain
            updated_transactions = []
            for tx in orig_open_transactions:
                updated_transaction = OrderedDict(
                    [
                        ("sender", tx["sender"]),
                        ("recipient", tx["recipient"]),
                        ("amount", tx["amount"]),
                    ]
                )
                updated_transactions.append(updated_transaction)
            open_transactions = updated_transactions
    except (IOError, IndexError) as e:
        print(f"Exception accessing file {blockchain_file_text} encountered: {e}")
        init_blockchain()


def load_data_pickle():
    """Initializes blockchain + open transactions data from a file."""
    global blockchain
    global open_transactions
    try:
        with open(blockchain_file_pickle, mode="rb") as f:
            file_content = pickle.loads(f.read())
            blockchain = file_content["blockchain"]
            open_transactions = file_content["open_transactions"]
    except (IOError, IndexError) as e:
        print(f"Exception accessing file {blockchain_file_pickle} encountered: {e}")
        init_blockchain()


load_data_json()


def save_data_json():
    """Saves blockchain + open transactions snapshot to a file."""
    try:
        with open(blockchain_file_text, mode="w") as f:
            f.write(json.dumps(blockchain))
            f.write("\n")
            f.write(json.dumps(open_transactions))
    except IOError as e:
        print(f"Saving file {blockchain_file_text} failed: {e}")


def save_data_pickle():
    """Saves blockchain + open transactions snapshot to a file."""
    try:
        with open(blockchain_file_pickle, mode="wb") as f:
            save_data = {
                "blockchain": blockchain,
                "open_transactions": open_transactions,
            }
            f.write(pickle.dumps(save_data))
    except IOError as e:
        print(f"Saving file {blockchain_file_pickle} failed: {e}")


def valid_proof(transactions, last_hash, proof):
    """Validates the proof: Does hash(last_hash, proof) contain 2 leading zeros?

    Arguments:
        :transactions: The transactions of the block for which the proof is created.
        :last_hash: The previous block's hash which will be stored in the current block.
        :proof: The proof number we're testing.
    """
    guess = (str(transactions) + str(last_hash) + str(proof)).encode()
    guess_hash = hash_string_256(guess)
    return guess_hash[0:2] == "00"


def proof_of_work():
    """Generate a proof of work for the open transactions, the hash of the previous block and a random number
    (which is guessed until it fits).
    """
    last_block = blockchain[-1]
    last_hash = hash_block(last_block)
    proof = 0
    while not valid_proof(open_transactions, last_hash, proof):
        proof += 1
    return proof


def get_balance(participant):
    """Calculate and return the balance for a participant.

    Arguments:
        :participant: The person for whom to calculate the balance.
    """
    tx_sender = [
        [tx["amount"] for tx in block["transactions"] if tx["sender"] == participant]
        for block in blockchain
    ]
    # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the
    # sender) This fetches sent amounts of open transactions (to avoid double spending)
    open_tx_sender = [
        tx["amount"] for tx in open_transactions if tx["sender"] == participant
    ]
    tx_sender.append(open_tx_sender)
    amount_sent = functools.reduce(
        lambda tx_sum, tx_amount: tx_sum + sum(tx_amount)
        if len(tx_amount) > 0
        else tx_sum,
        tx_sender,
        0,
    )
    # This fetches received coin amounts of transactions that were already included in blocks of the blockchain We
    # ignore open transactions here because you shouldn't be able to spend coins before the transaction was confirmed
    # + included in a block
    tx_recipient = [
        [tx["amount"] for tx in block["transactions"] if tx["recipient"] == participant]
        for block in blockchain
    ]
    amount_received = functools.reduce(
        lambda tx_sum, tx_amount: tx_sum + sum(tx_amount)
        if len(tx_amount) > 0
        else tx_sum,
        tx_recipient,
        0,
    )
    # Return the total balance
    return amount_received - amount_sent


def get_last_blockchain_value():
    """Returns the last value of the current blockchain."""
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def verify_transaction(transaction):
    """Verify a transaction by checking whether the sender has sufficient coins."""
    sender_balance = get_balance(transaction["sender"])
    return sender_balance >= transaction["amount"]


def add_transaction(recipient, sender=owner, amount=1.0):
    """Append a new value as well as the last blockchain value to the blockchain

    Arguments:
        :sender: The sender of the coins.
        :recipient: The recipient of the coins.
        :amount: The amount of coins sent with the transaction (default = 1.0)
    """
    # transaction = {
    #     "sender": sender,
    #     "recipient": recipient,
    #     "amount": amount
    # }
    transaction = OrderedDict(
        [("sender", sender), ("recipient", recipient), ("amount", amount)]
    )
    if verify_transaction(transaction):
        open_transactions.append(transaction)
        participants.add(sender)
        participants.add(recipient)
        save_data_json()
        return True
    return False


def mine_block():
    """Create a new block and add open transactions to it."""
    # Fetch the currently last block of the blockchain
    last_block = get_last_blockchain_value()
    # Hash the last block (=> to be able to compare it to the stored hash value)
    hashed_block = hash_block(last_block)
    proof = proof_of_work()
    # reward_transaction = {
    #     "sender": "MINING",
    #     "recipient": owner,
    #     "amount": MINING_REWARD
    # }
    reward_transaction = OrderedDict(
        [("sender", "MINING"), ("recipient", owner), ("amount", MINING_REWARD)]
    )
    # Copy transaction instead of manipulating the original open_transactions list
    # This ensures that if for some reason the mining should fail, we don't have the reward transaction stored in the
    copied_open_transactions = open_transactions[:]
    copied_open_transactions.append(reward_transaction)
    block = {
        "previous_hash": hashed_block,
        "index": len(blockchain),
        "transactions": copied_open_transactions,
        "proof": proof,
    }
    blockchain.append(block)
    return True


def get_transaction_value():
    """Returns the input of the user (a new transaction amount) as a float."""
    tx_recepient = input("Enter the recepient of the transaction: ")
    tx_amount = float(input("Your transaction amount please: "))
    return tx_recepient, tx_amount


def get_user_choice():
    """Prompts the user for its choice and return it."""
    user_input = input("Your choice: ")
    return user_input


def print_blockchain_elements():
    """Output all blocks of the blockchain."""
    # Output the blockchain list to the console
    for block in blockchain:
        print("Outputting Block")
        print(block)
    else:
        print("-" * 20)


def verify_chain():
    """Verify the current blockchain and return True if it's valid, False otherwise"""
    for index, block in enumerate(blockchain):
        if index == 0:
            continue
        if block["previous_hash"] != hash_block(blockchain[index - 1]):
            return False
        if not valid_proof(
            block["transactions"][:-1], block["previous_hash"], block["proof"]
        ):
            print("Proof of work is invalid!")
            return False
    return True


def verify_open_transactions():
    """Verifies all open transactions."""
    return all([verify_transaction(tx) for tx in open_transactions])


waiting_for_input = True

# Main loop for the user interface
while waiting_for_input:
    print("Please choose")
    print("1: Add a new transaction value")
    print("2: Mine a new block")
    print("3: Output the blockchain blocks")
    print("4: Output participants")
    print("5: Check open transaction validity")
    print("h: Manipulate the chain")
    print("q: Quit")
    user_choice = get_user_choice()
    match user_choice:
        case "1":
            recepient, amount = get_transaction_value()
            if add_transaction(recepient, amount=amount):
                print("Added transaction!")
            else:
                print("Transaction failed!")
            print(open_transactions)
        case "2":
            if mine_block():
                open_transactions = []
                save_data_json()
        case "3":
            print_blockchain_elements()
        case "4":
            print(participants)
        case "5":
            if verify_open_transactions():
                print("All transactions are valid!")
            else:
                print("There are invalid transactions!")
        case "h":
            if len(blockchain) >= 1:
                blockchain[0] = {
                    "previous_hash": "",
                    "index": 0,
                    "transactions": [
                        {"sender": "Gyula", "recipient": "Enikő", "amount": 10.0}
                    ],
                }
        case "q":
            waiting_for_input = False
        case _:
            print("Input was invalid, please pick a value from the list!")
    if not verify_chain():
        print_blockchain_elements()
        print("Invalid blockchain!")
        waiting_for_input = False
    print(f"Balance of {owner} is {get_balance(owner):6.2f}")
