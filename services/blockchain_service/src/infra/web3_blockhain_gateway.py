import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
from eth_account import Account

from src.domain.ports.blockhain_gateway import BlockchainGatewayPort
from src.domain.ports.nonce_manager import NonceManagerPort


class Web3BlockchainGateway(BlockchainGatewayPort):
    def __init__(
            self,
            node_url: str,
            private_key: str,
            nonce_manager: NonceManagerPort,
            chain_id: int = 11155111
    ):
        """
        :param node_url: RPC URL (например, от Infura или Alchemy)
        :param private_key: Приватный ключ кошелька, который платит газ
        :param nonce_manager: Порт для управления счетчиком транзакций (Redis)
        :param chain_id: ID сети (1=Mainnet, 137=Polygon, 11155111=Sepolia)
        """
        self._w3 = AsyncWeb3(AsyncHTTPProvider(node_url))
        self._account = Account.from_key(private_key)
        self._nonce_manager = nonce_manager
        self._chain_id = chain_id
        self._logger = logging.getLogger(self.__class__.__name__)

    async def send_transaction(self, payload: Dict[str, Any]) -> str:
        """
        Отправляет транзакцию с данными payload.
        Включает механизм автоматического восстановления nonce (Retry).
        """
        try:
            payload_json = json.dumps(payload)
            data_hex = self._w3.to_hex(text=payload_json)

            gas_price = await self._w3.eth.gas_price

            try:
                return await self._execute_tx(data_hex, gas_price)

            except ValueError as e:
                error_msg = str(e).lower()
                if "nonce" in error_msg or "replacement" in error_msg:
                    self._logger.warning(
                        f"Nonce sync issue detected ({error_msg}). Resyncing from chain and retrying...")

                    await self._nonce_manager.sync_from_chain(self._account.address)

                    return await self._execute_tx(data_hex, gas_price)

                raise e

        except Exception as e:
            self._logger.error(f"Failed to send transaction: {e}")
            raise

    async def _execute_tx(self, data_hex: str, gas_price: int) -> str:
        """Внутренний метод: получить nonce -> подписать -> отправить"""
        nonce = await self._nonce_manager.get_next_nonce(self._account.address)

        tx_params = {
            'nonce': nonce,
            'to': self._account.address,
            'value': 0,
            'gas': 100000,
            'gasPrice': gas_price,
            'chainId': self._chain_id,
            'data': data_hex
        }

        signed_tx = self._account.sign_transaction(tx_params)

        tx_hash_bytes = await self._w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash = self._w3.to_hex(tx_hash_bytes)

        self._logger.info(f"Transaction sent: {tx_hash} | Nonce: {nonce}")
        return tx_hash

    async def get_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет статус транзакции в блокчейне.
        """
        try:
            receipt = await self._w3.eth.get_transaction_receipt(tx_hash)

            block = await self._w3.eth.get_block(receipt['blockNumber'])

            latest_block = await self._w3.eth.block_number
            confirmations = latest_block - receipt['blockNumber']

            return {
                "block_number": receipt['blockNumber'],
                "confirmations": confirmations,
                "timestamp": datetime.fromtimestamp(block['timestamp']).isoformat(),
                "status": "success" if receipt['status'] == 1 else "failed",
                "gas_used": receipt['gasUsed']
            }
        except TransactionNotFound:
            return None
        except Exception as e:
            self._logger.error(f"Error fetching receipt: {e}")
            return None
