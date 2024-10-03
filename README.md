# Qoin-Py-Client-PQ

This is a Python implementation of a blockchain node that utilizes post-quantum cryptography. It serves as a proof of concept, demonstrating how more secure cryptographic functions can be integrated into blockchain systems while maintaining robustness and practicality.

I developed this client as part of my submission for **NYCHAQ**, the first multi-school quantum computing hackathon in NYC, in which my team won first place for the security challenge.

## Design

Each node operates with its own local SQLite database, where it stores transaction and block data. The consensus mechanism adopts a hybrid approach, utilizing both pre-quantum and post-quantum cryptographic functions. This design decision was made to strike a balance between security and practicality.

Ideally, a proper blockchain node would connect directly to other nodes in a peer-to-peer network. However, considering that this hackathon only spanned a week, developing a mechanism for node discovery wasn’t feasible. As a result, this client relies on a centralized relay server, which allows nodes to communicate and synchronize their states. 

Despite this reliance on a central server, nodes do not blindly accept blocks. They independently verify each block before adding it to their database. This leads to consensus among nodes, as the system is a Proof of Work (PoW) implementation, ensuring that nodes converge on the longest valid blockchain.

To learn more about the motivation, implementation, and design, please visit the relay server repo at the following link: [Relay Server Repository](https://github.com/kdukuray/Qoin-Relay-Server).

## Setup

To use this client, you need to connect it to a relay server. In the `blockchain.py` file, there's a variable called `base_url` that defines the root route to the relay server. You can change this route to point to wherever your relay server is running.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kdukuray/Qoin-Py-Client-PQ
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the client:
   ```bash
   python3 main.py
   ```

### Important Note:

If you encounter issues with the `pqcrypto` library, it may be due to missing compiled C bindings for some cryptographic functions. To resolve this:

1. Navigate to the `site-packages` folder within your virtual environment.
2. Run the following command:
   ```bash
   sudo python3 compile.py
   ```

This should resolve any compilation issues.

## License

This project is open-source, licensed under the MIT License. Feel free to use, modify, and contribute.
