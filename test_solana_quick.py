"""
Test Solana logger with persistent keypair.

1. Run: python test_solana_quick.py
2. It prints a wallet address — go to https://faucet.solana.com, paste it, select Devnet, request SOL
3. Run again: python test_solana_quick.py
4. This time it uses the same wallet (already funded) and logs the event
"""
import sys, asyncio, base64, os, json
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

KEYFILE = 'test_solana_wallet.json'

def get_or_create_keypair() -> Keypair:
    if os.path.exists(KEYFILE):
        with open(KEYFILE) as f:
            data = json.load(f)
        kp = Keypair.from_bytes(base64.b64decode(data['key']))
        print(f'Loaded existing wallet: {kp.pubkey()}')
        return kp

    kp = Keypair()
    with open(KEYFILE, 'w') as f:
        json.dump({'key': base64.b64encode(bytes(kp)).decode()}, f)
    print(f'Created new wallet: {kp.pubkey()}')
    return kp

async def test():
    kp = get_or_create_keypair()

    client = AsyncClient("https://api.devnet.solana.com")
    bal = await client.get_balance(kp.pubkey())
    lamports = bal.value
    print(f'Balance: {lamports / 1e9:.4f} SOL')

    if lamports == 0:
        print(f'\nWallet has no SOL. Go to https://faucet.solana.com')
        print(f'Paste this address: {kp.pubkey()}')
        print(f'Select Devnet, request 1 SOL, then run this script again.')
        return

    from services.solana_logger import SolanaLogger
    s = SolanaLogger()
    s.payer = kp
    s._funded = True

    print('Logging event...')
    tx = await s.log_event('test-cam', 1745600000.0, 'Person took package from doorstep')
    print(f'\nView on Solana Explorer:')
    print(f'https://explorer.solana.com/tx/{tx}?cluster=devnet')

asyncio.run(test())
