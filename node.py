from flask import Flask, jsonify, request
from flask_cors import CORS

from blockchain import Blockchain
from wallet import Wallet

app = Flask(__name__)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)
CORS(app)


@app.route("/wallet", methods=["POST"])
def create_keys():
    """Creates a new pair of private and public keys."""
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            "message": "Keys created and saved.",
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {"message": "Saving the keys failed."}
        return jsonify(response), 500


@app.route("/wallet", methods=["GET"])
def load_keys():
    """Loads the keys from the wallet.txt file into the wallet."""
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            "message": "Keys loaded.",
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {"message": "Loading the keys failed."}
        return jsonify(response), 500


@app.route("/balance", methods=["GET"])
def get_balance():
    """Gets and returns the balance of the sender's address."""
    balance = blockchain.get_balance()
    if balance is not None:
        response = {
            "message": "Fetched balance successfully.",
            "funds": balance,
        }
        return jsonify(response), 200
    else:
        response = {
            "message": "Loading balance failed.",
            "wallet_set_up": wallet.public_key is not None,
        }
        return jsonify(response), 500


@app.route("/transaction", methods=["POST"])
def add_transaction():
    """Adds a transaction to the open transactions list."""
    if wallet.public_key is None:
        response = {"message": "No wallet set up."}
        return jsonify(response), 400
    values = request.get_json()
    if not values:
        response = {"message": "No data found."}
        return jsonify(response), 400
    required_fields = ["recipient", "amount"]
    if not all(field in values for field in required_fields):
        response = {"message": "Required data is missing."}
        return jsonify(response), 400
    recipient, amount = values["recipient"], values["amount"]
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    if blockchain.add_transaction(recipient, wallet.public_key, signature, amount):
        response = {
            "message": "Successfully added transaction.",
            "transaction": {
                "sender": wallet.public_key,
                "recipient": recipient,
                "amount": amount,
                "signature": signature,
            },
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {"message": "Creating a transaction failed."}
        return jsonify(response), 500


@app.route("/mine", methods=["POST"])
def mine():
    """Function to be called by the miner thread."""
    block = blockchain.mine_block()
    if block is not None:
        dict_block = block.__dict__.copy()
        dict_block["transactions"] = [tx.__dict__ for tx in dict_block["transactions"]]
        response = {
            "message": "Block added successfully.",
            "block": dict_block,
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {
            "message": "Adding a block failed.",
            "wallet_set_up": wallet.public_key is not None,
        }
        return jsonify(response), 500


@app.route("/chain", methods=["GET"])
def get_chain():
    """Returns the full blockchain and its current length."""
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block["transactions"] = [tx.__dict__ for tx in dict_block["transactions"]]
    return jsonify(dict_chain), 200


@app.route("/", methods=["GET"])
def get_ui():
    """Returns the homepage."""
    return """
    <h1>Blockchain</h1>
    <p>Choose a transaction type:</p>
    <ul>
        <li><a href="/balance">Balance</a></li>
        <li><a href="/chain">Chain</a></li>
        <li><a href="/wallet">Wallet</a></li>
    </ul>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
