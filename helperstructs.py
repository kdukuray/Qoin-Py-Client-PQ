class BlockStruct:
    def __init__(self, block_id, block_hash, prev_block_hash):
        self.block_id = block_id
        self.block_hash = block_hash
        self.prev_block_hash = prev_block_hash

    def print(self):
        print(f"""
        Block Id: {self.block_id},
        Block Hash: {self.block_hash},
        Pre Block Hash: {self.prev_block_hash}
""")


