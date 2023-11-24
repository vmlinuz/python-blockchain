from flask import Flask, jsonify, request
from flask_cors import CORS

from blockchain import Blockchain
from wallet import Wallet

app = Flask(__name__)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)
CORS(app)


@app.route("/", methods=["GET"])
def get_ui():
    return """
    <h1>Blockchain</h1>
    <p>Choose a transaction type:</p>
    <ul>
        <li><a href="/chain">Chain</a></li>
    </ul>
    """


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)