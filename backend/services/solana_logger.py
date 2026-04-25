import asyncio
import base64
import hashlib
import json
import logging
import os
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.instruction import Instruction, AccountMeta
from solders.message import Message

logger = logging.getLogger(__name__)

MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
DEVNET_RPC = "https://api.devnet.solana.com"


def _load_or_create_keypair() -> Keypair:
    """Load keypair from SOLANA_PRIVATE_KEY env var, or generate a new one and print it."""
    key_b64 = os.getenv("SOLANA_PRIVATE_KEY")
    if key_b64:
        try:
            raw = base64.b64decode(key_b64)
            kp = Keypair.from_bytes(raw)
            logger.info("Loaded Solana keypair from env: %s", kp.pubkey())
            return kp
        except Exception:
            logger.exception("Invalid SOLANA_PRIVATE_KEY, generating new keypair")

    kp = Keypair()
    encoded = base64.b64encode(bytes(kp)).decode()
    logger.info("Generated new Solana keypair: %s", kp.pubkey())
    logger.info("To reuse across restarts, add to .env:  SOLANA_PRIVATE_KEY=%s", encoded)
    return kp


class SolanaLogger:
    def __init__(self):
        self.client = AsyncClient(DEVNET_RPC)
        self.payer = _load_or_create_keypair()
        self._funded = False

    async def fund_wallet(self, retries: int = 5):
        """Ensure wallet has SOL. Skips airdrop if already funded."""
        try:
            bal = await self.client.get_balance(self.payer.pubkey())
            if bal.value > 0:
                logger.info("Wallet already funded: %.4f SOL", bal.value / 1e9)
                self._funded = True
                return
        except Exception:
            pass

        for attempt in range(retries):
            try:
                sig = await self.client.request_airdrop(self.payer.pubkey(), 1_000_000_000)
                await self.client.confirm_transaction(sig.value)
                self._funded = True
                return
            except Exception:
                pass

            try:
                import httpx
                async with httpx.AsyncClient(timeout=15) as http:
                    resp = await http.post(
                        "https://faucet.solana.com/api/request-airdrop",
                        json={"wallet": str(self.payer.pubkey()), "network": "devnet", "amount": 1},
                    )
                    if resp.status_code == 200:
                        await asyncio.sleep(3)
                        self._funded = True
                        return
            except Exception:
                pass

            if attempt == retries - 1:
                raise RuntimeError("Could not fund wallet after all retries")
            await asyncio.sleep(2 ** attempt)

    def hash_event(self, camera_id: str, timestamp: float, description: str) -> str:
        data = json.dumps({
            "camera_id": camera_id,
            "timestamp": timestamp,
            "description": description,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    async def log_event(self, camera_id: str, timestamp: float, description: str) -> str:
        event_hash = self.hash_event(camera_id, timestamp, description)

        memo_ix = Instruction(
            program_id=MEMO_PROGRAM_ID,
            accounts=[AccountMeta(pubkey=self.payer.pubkey(), is_signer=True, is_writable=False)],
            data=event_hash.encode("utf-8"),
        )

        bh_resp = await self.client.get_latest_blockhash()
        blockhash = bh_resp.value.blockhash

        msg = Message.new_with_blockhash([memo_ix], self.payer.pubkey(), blockhash)
        tx = Transaction.new_unsigned(msg)
        tx.sign([self.payer], blockhash)

        result = await self.client.send_transaction(tx)
        return str(result.value)
