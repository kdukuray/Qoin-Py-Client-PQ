from blockchain import *
from InquirerPy import prompt

qoin = BlockChain()
user = Wallet(0, "", "")


def load_existing_wallet():
    global user
    print("Loading existing wallet...")
    credentials = [
        {
            "type": "input",
            "name": "private_key",
            "message": "Enter your private key:",
        },
        {
            "type": "password",
            "name": "pubic_key",
            "message": "Enter your public key:",
        }
    ]
    creds = prompt(credentials)
    # Load existing wallet
    print("Loading existing wallet...")
    resp = requests.get(f"http://127.0.0.1:8000/postquantum/wallets/{creds['private_key']}/")
    resp = resp.json()
    user = Wallet(resp.get("wallet_id"), creds["private_key"], creds["public_key"])
    print(f"Wallet Info ~ Private key: \n{user.private_key}, Public Key: \n{user.public_key}")


def create_new_wallet():
    global user
    # Create a new wallet
    print("Creating a new wallet...")
    resp = requests.get("http://127.0.0.1:8000/postquantum/wallets/new/")
    resp = resp.json()
    print(resp.get("wallet_id"))
    user = Wallet(resp.get("wallet_id"), resp.get("private_key"), resp.get("public_key"))
    print(f"Wallet Info ~ Private key: \n{user.private_key}, Public Key: \n{user.public_key}")


def display_current_blockchain_state():
    print("Current Blockchain State:")
    qoin.get_and_verify_current_block_chain_state()
    qoin.print_current_chain_sate()


def make_transaction():
    print("Making a new transaction...")
    transaction = [
        {
            "type": "input",
            "name": "recipient",
            "message": "Enter the recipient address:",
        },
        {
            "type": "input",
            "name": "amount",
            "message": "Enter the amount to send:",
        }
    ]
    trxn = prompt(transaction)
    user.make_transaction(trxn["recipient"], int(trxn["amount"]))
    print(f"Transaction to {trxn['recipient']} for {trxn['amount']} added to pending transactions.")


def display_pending_transactions():
    qoin.get_pending_transactions()


def mine_block():
    print("Getting Latest BlockChain Snapshot")
    qoin.get_and_verify_current_block_chain_state()
    print("Mining a new block...")
    qoin.mine_block(user.wallet_id)
    print("Block mined and broadcast to the Network.")


def show_wallet_menu():
    while True:
        wallet_menu = [
            {
                "type": "list",
                "message": f"Current Balance: {user.get_wallet_balance()}\nSelect an option:",
                "choices": [
                    "Display Current Blockchain State",
                    "Make a Transaction",
                    "Display Pending Transactions",
                    "Mine Block",
                    "Exit"
                ],
                "name": "wallet_command"
            }
        ]
        result = prompt(wallet_menu)

        if result["wallet_command"] == "Display Current Blockchain State":
            display_current_blockchain_state()
        elif result["wallet_command"] == "Make a Transaction":
            make_transaction()
        elif result["wallet_command"] == "Display Pending Transactions":
            display_pending_transactions()
        elif result["wallet_command"] == "Mine Block":
            mine_block()
        elif result["wallet_command"] == "Exit":
            print("Exiting the wallet.")
            break


# Main program
menu = [
    {
        "type": "list",
        "message": "Welcome to Qoin's Python Client (beta).",
        "choices": ["Create a New Wallet", "Load An Existing Wallet"],
        "name": "initial_command"
    },
]

result = prompt(menu)
if result["initial_command"] == "Create a New Wallet":
    create_new_wallet()
elif result["initial_command"] == "Load An Existing Wallet":
    load_existing_wallet()


# After loading or creating a wallet, show the wallet menu
show_wallet_menu()


