import hashlib
import socket
import json
import time
import os

# Configure your mining pool and worker details
POOL_ADDRESS = "stratum+tcp://eu.stratum.slushpool.com:3333"
WALLET_ADDRESS = "bc1q7mqlpml5kyju0mx0vxqlyl0zp58dnlww79zswc"
WORKER_NAME = os.getlogin()  # Use the Windows username dynamically
PASSWORD = "x"  # Commonly set to "x" in most pools


def connect_to_pool():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((POOL_ADDRESS.split(":")[1][2:], int(POOL_ADDRESS.split(":")[2])))
    return sock


def subscribe(sock):
    request = json.dumps({"id": 1, "method": "mining.subscribe", "params": []}) + "\n"
    sock.send(request.encode())
    response = sock.recv(1024).decode()
    return json.loads(response)["result"]


def authorize(sock):
    request = json.dumps(
        {"id": 2, "method": "mining.authorize", "params": [WALLET_ADDRESS + "." + WORKER_NAME, PASSWORD]}) + "\n"
    sock.send(request.encode())
    response = sock.recv(1024).decode()
    return json.loads(response)["result"]


def mine(sock, extranonce1, extranonce2, job_id, previous_hash, coinbase1, coinbase2, merkle_branch, version, nbits,
         ntime):
    nonce = 0
    while True:
        coinbase = coinbase1 + extranonce1 + extranonce2 + coinbase2
        coinbase_hash_bin = hashlib.sha256(hashlib.sha256(coinbase.encode()).digest()).digest()
        merkle_root = coinbase_hash_bin
        for h in merkle_branch:
            merkle_root = hashlib.sha256(hashlib.sha256(merkle_root + bytes.fromhex(h)).digest()).digest()

        blockheader = (version + previous_hash + merkle_root.hex() + nbits + ntime + hex(nonce)[2:].zfill(8)).encode()
        block_hash = hashlib.sha256(hashlib.sha256(blockheader).digest()).hexdigest()

        if block_hash.startswith("000000"):
            print(f"Found block with nonce {nonce}!")
            return

        nonce += 1
        if nonce % 100000 == 0:
            time.sleep(0.1)


def main():
    sock = connect_to_pool()
    extranonce1, extranonce2 = subscribe(sock)
    authorized = authorize(sock)

    while True:
        response = sock.recv(1024).decode()
        job = json.loads(response)

        if job["method"] == "mining.notify":
            params = job["params"]
            job_id, previous_hash, coinbase1, coinbase2, merkle_branch, version, nbits, ntime, clean_jobs = params
            mine(sock, extranonce1, extranonce2, job_id, previous_hash, coinbase1, coinbase2, merkle_branch, version,
                 nbits, ntime)


if __name__ == "__main__":
    main()
