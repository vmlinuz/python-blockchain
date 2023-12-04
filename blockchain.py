"""Provides the Blockchain class."""

import functools
import json
import pickle

import requests

from block import Block
from transaction import Transaction
from utility.hash_util import hash_block
from utility.verification import Verification
from wallet import Wallet

# The reward we give to miners (for creating a new block)
MINING_REWARD = 10


class Blockchain:
    """The Blockchain class manages the chain of blocks as well as open transactions and the node on which it's
    running.
    """

    def __init__(self, public_key, node_id):
        """The constructor for the Blockchain class."""
        # Our starting block for the blockchain
        genesis_block = Block(0, "", [], 100, 0)
        # Initializing our (empty) blockchain list
        self.__chain = [genesis_block]
        # Unhandled transactions
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.blockchain_file_text = f"blockchain-{node_id}.txt"
        self.blockchain_file_pickle = f"blockchain-{node_id}.pickle"
        self.resolve_conflicts = False
        self.load_data_json()

    @property
    def chain(self):
        """Returns a copy of the blockchain list."""
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        """The chain is immutable from outside the class."""
        pass

    @property
    def open_transactions(self):
        """Returns a copy of the open transactions list."""
        return self.__open_transactions[:]

    @open_transactions.setter
    def open_transactions(self, val):
        """The open_transactions is immutable from outside the class."""
        pass

    def load_data_json(self):
        """Initializes blockchain + open transactions data from a file."""
        try:
            with open(self.blockchain_file_text, mode="r") as f:
                file_content = f.readlines()
                orig_blockchain = json.loads(file_content[0][:-1])
                orig_open_transactions = json.loads(file_content[1][:-1])
                updated_blockchain = []
                for block in orig_blockchain:
                    converted_trasactions = [
                        Transaction(
                            tx["sender"],
                            tx["recipient"],
                            tx["signature"],
                            tx["amount"],
                        )
                        for tx in block["transactions"]
                    ]
                    updated_block = Block(
                        block["index"],
                        block["previous_hash"],
                        converted_trasactions,
                        block["proof"],
                        block["timestamp"],
                    )
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                updated_transactions = []
                for tx in orig_open_transactions:
                    updated_transaction = Transaction(
                        tx["sender"],
                        tx["recipient"],
                        tx["signature"],
                        tx["amount"],
                    )
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError) as e:
            print(
                f"Exception accessing file {self.blockchain_file_text} encountered: {e}"
            )

    def load_data_pickle(self):
        """Initializes blockchain + open transactions data from a file."""
        try:
            with open(self.blockchain_file_pickle, mode="rb") as f:
                file_content = pickle.loads(f.read())
                self.__chain = file_content["blockchain"]
                self.__open_transactions = file_content["open_transactions"]
        except (IOError, IndexError) as e:
            print(
                f"Exception accessing file {self.blockchain_file_pickle} encountered: {e}"
            )

    def save_data_json(self):
        """Saves blockchain + open transactions snapshot to a file."""
        try:
            with open(self.blockchain_file_text, mode="w") as f:
                saveable_blockchain = [
                    block.__dict__
                    for block in [
                        Block(
                            block_el.index,
                            block_el.previous_hash,
                            [tx.__dict__ for tx in block_el.transactions],
                            block_el.proof,
                            block_el.timestamp,
                        )
                        for block_el in self.__chain
                    ]
                ]
                f.write(json.dumps(saveable_blockchain))
                f.write("\n")
                saveable_transactions = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_transactions))
                f.write("\n")
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError as e:
            print(f"Saving file {self.blockchain_file_text} failed: {e}")

    def save_data_pickle(self):
        """Saves blockchain + open transactions snapshot to a file."""
        try:
            with open(self.blockchain_file_pickle, mode="wb") as f:
                save_data = {
                    "blockchain": self.__chain,
                    "open_transactions": self.__open_transactions,
                }
                f.write(pickle.dumps(save_data))
        except IOError as e:
            print(f"Saving file {self.blockchain_file_pickle} failed: {e}")

    def proof_of_work(self):
        """Generate a proof of work for the open transactions, the hash of the previous block and a random number
        (which is guessed until it fits).
        """
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        """Calculate and return the balance for a participant."""
        if sender is None:
            if self.public_key is None:
                return None
            participant = self.public_key
        else:
            participant = sender
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the
        # sender) This fetches sent amounts of transactions that were already included in blocks of the blockchain
        tx_sender = [
            [tx.amount for tx in block.transactions if tx.sender == participant]
            for block in self.__chain
        ]
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the
        # sender) This fetches sent amounts of open transactions (to avoid double spending)
        open_tx_sender = [
            tx.amount for tx in self.__open_transactions if tx.sender == participant
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
            [tx.amount for tx in block.transactions if tx.recipient == participant]
            for block in self.__chain
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

    def get_last_blockchain_value(self):
        """Returns the last value of the current blockchain."""
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(
        self, recipient, sender, signature, amount=1.0, is_receiving=False
    ):
        """Append a new value as well as the last blockchain value to the blockchain

        Arguments:
            :sender: The sender of the coins.
            :recipient: The recipient of the coins.
            :signature: The signature of the transaction.
            :amount: The amount of coins sent with the transaction (default = 1.0)
        """
        # transaction = {
        #     "sender": sender,
        #     "recipient": recipient,
        #     "amount": amount
        # }
        if self.public_key is None:
            return False
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data_json()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = f"http://{node}/broadcast-transaction"
                    try:
                        response = requests.post(
                            url,
                            json={
                                "sender": sender,
                                "recipient": recipient,
                                "amount": amount,
                                "signature": signature,
                            },
                        )
                        if response.status_code == 400 or response.status_code == 500:
                            print("Transaction declined, needs resolving")
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self):
        """Create a new block and add open transactions to it."""
        # Fetch the currently last block of the blockchain
        if self.public_key is None:
            return None
        last_block = self.get_last_blockchain_value()
        # Hash the last block (=> to be able to compare it to the stored hash value)
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        # Miners should be rewarded, so let's create a reward transaction
        reward_transaction = Transaction("MINING", self.public_key, "", MINING_REWARD)
        # Copy transaction instead of manipulating the original open_transactions list
        # This ensures that if for some reason the mining should fail, we don't have the reward transaction stored in the
        # open transactions
        copied_open_transactions = self.__open_transactions[:]
        for tx in copied_open_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_open_transactions.append(reward_transaction)
        block = Block(
            len(self.__chain),
            hashed_block,
            copied_open_transactions,
            proof,
        )
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data_json()
        for node in self.__peer_nodes:
            url = f"http://{node}/broadcast-block"
            converted_block = block.__dict__.copy()
            converted_block["transactions"] = [
                tx.__dict__ for tx in converted_block["transactions"]
            ]
            try:
                response = requests.post(url, json={"block": converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print("Block declined, needs resolving")
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        """Adds a block mined by someone else to the local blockchain."""
        transactions = [
            Transaction(
                tx["sender"],
                tx["recipient"],
                tx["signature"],
                tx["amount"],
            )
            for tx in block["transactions"]
        ]
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block["previous_hash"], block["proof"]
        )
        hashes_match = hash_block(self.chain[-1]) == block["previous_hash"]
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(
            block["index"],
            block["previous_hash"],
            transactions,
            block["proof"],
            block["timestamp"],
        )
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        for incoming_tx in block["transactions"]:
            for open_tx in stored_transactions:
                if (
                    open_tx.sender == incoming_tx["sender"]
                    and open_tx.recipient == incoming_tx["recipient"]
                    and open_tx.amount == incoming_tx["amount"]
                    and open_tx.signature == incoming_tx["signature"]
                ):
                    try:
                        self.__open_transactions.remove(open_tx)
                    except ValueError:
                        print("Item was already removed")
        self.save_data_json()
        return True

    def resolve(self):
        """Resolves conflicts between blockchain nodes by replacing our chain with the longest one in the network."""
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = f"http://{node}/chain"
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [
                    Block(
                        block["index"],
                        block["previous_hash"],
                        [
                            Transaction(
                                tx["sender"],
                                tx["recipient"],
                                tx["signature"],
                                tx["amount"],
                            )
                            for tx in block["transactions"]
                        ],
                        block["proof"],
                        block["timestamp"],
                    )
                    for block in node_chain
                ]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if (
                    node_chain_length > local_chain_length
                    and Verification.verify_chain(node_chain)
                ):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.__chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data_json()
        return replace

    def add_peer_node(self, node):
        """Adds a new node to the peer node set.

        Arguments:
            :node: The node URL which should be added.
        """
        self.__peer_nodes.add(node)
        self.save_data_json()

    def remove_peer_node(self, node):
        """Removes a node from the peer node set.

        Arguments:
            :node: The node URL which should be removed.
        """
        self.__peer_nodes.discard(node)
        self.save_data_json()

    def get_peer_nodes(self):
        """Return a list of all connected peer nodes."""
        return list(self.__peer_nodes)
