import asyncio
import json
import logging
import time
from types import coroutine
from collections import deque

from pytoniq_core import Cell, Slice, MessageAny, Transaction, Address
from pytoniq_core.tlb.block import ExtBlkRef

from pytoniq.liteclient import RunGetMethodError
from pytoniq.liteclient import LiteClient, RunGetMethodError
from pytoniq_core.tlb import Block, ValueFlow, ShardAccounts
from pytoniq_core.tl import BlockIdExt
from pytoniq.liteclient.balancer import LiteBalancer

from jettons import get_jetton_data, get_wallet_data


class BlockScanner:

    def __init__(self,
                 client: LiteClient,
                 block_handler: coroutine
                 ):
        """
        :param client: LiteClient
        :param block_handler: function to be called on new block
        """
        self.client = client
        self.block_handler = block_handler
        self.shards_storage = {}
        self.blks_dequeue = deque()
        self.inited = False

    async def run(self):
        if not self.client.inited:
            raise Exception('should init client first')
        master_blk = self.mc_info_to_tl_blk(await self.client.get_masterchain_info())
        if not self.inited:
            shards = await self.client.get_all_shards_info(master_blk)
            for shard in shards:
                self.shards_storage[self.get_shard_id(shard)] = shard.seqno
                self.blks_dequeue.append(shard)
            self.inited = True
        while True:
            self.blks_dequeue.append(master_blk)

            shards = await self.client.get_all_shards_info(master_blk)
            for shard in shards:
                await self.get_not_seen_shards(shard)
                self.shards_storage[self.get_shard_id(shard)] = shard.seqno

            tasks = []
            while self.blks_dequeue:
                tasks.append(self.block_handler(self.blks_dequeue.pop()))

            await asyncio.gather(*tasks)

            last_seqno = master_blk.seqno
            while True:
                new_master_blk = self.mc_info_to_tl_blk(await self.client.get_masterchain_info_ext())
                if new_master_blk.seqno != last_seqno:
                    master_blk = new_master_blk
                    break

    async def get_not_seen_shards(self, shard: BlockIdExt):
        if self.shards_storage.get(self.get_shard_id(shard)) == shard.seqno:
            return []
        result = []
        self.blks_dequeue.append(shard)
        full_blk = await self.client.raw_get_block_header(shard)
        prev_ref = full_blk.info.prev_ref
        if prev_ref.type_ == 'prev_blk_info':  # only one prev block
            prev: ExtBlkRef = prev_ref.prev
            await self.get_not_seen_shards(BlockIdExt(
                    workchain=shard.workchain, seqno=prev.seqno, shard=shard.shard,
                    root_hash=prev.root_hash, file_hash=prev.file_hash
                )
            )
        else:
            prev1: ExtBlkRef = prev_ref.prev1
            prev2: ExtBlkRef = prev_ref.prev2
            await self.get_not_seen_shards(BlockIdExt(
                    workchain=shard.workchain, seqno=prev1.seqno, shard=shard.shard,
                    root_hash=prev1.root_hash, file_hash=prev1.file_hash
                )
            )
            await self.get_not_seen_shards(BlockIdExt(
                    workchain=shard.workchain, seqno=prev2.seqno, shard=shard.shard,
                    root_hash=prev2.root_hash, file_hash=prev2.file_hash
                )
            )
        return result

    @staticmethod
    def mc_info_to_tl_blk(info: dict):
        return BlockIdExt.from_dict(info['last'])

    @staticmethod
    def get_shard_id(blk: BlockIdExt):
        return f'{blk.workchain}:{blk.shard}'


async def define_type(address: Address):
    try:
        data = await client.run_get_method(address, 'get_wallet_data', [])
        return 'JETTON_WALLET', data
    except RunGetMethodError:
        pass
    try:
        data = await client.run_get_method(address, 'get_jetton_data', [])
        return 'JETTON_MINTER', data
    except RunGetMethodError:
        pass
    try:
        data = await client.run_get_method(address, 'get_nft_data', [])
        return 'NFT', data
    except RunGetMethodError:
        pass
    return '', []


async def handle_deploy(block, tr: Transaction):
    if tr.orig_status.type_ == 'nonexist' and tr.end_status.type_ == 'active':
        addr = Address((block.workchain, tr.account_addr))
        type_, _ = await define_type(addr)
        print('DEPLOY', addr, type_)
        if type_ == 'JETTON_WALLET':
            data = await get_wallet_data(client, addr)
            # print(data)
            jetton_data = await get_jetton_data(client, data['jetton_master_address'])
            # print(jetton_data)


async def handle_block(block: BlockIdExt):
    if block.workchain == -1:  # skip masterchain blocks
        return
    trs = await client.raw_get_block_transactions_ext(block)
    for tr in trs:
        await handle_deploy(block, tr)
        cs = tr.in_msg.body.begin_parse()
        if cs.remaining_bits >= 32:
            op_code = cs.load_uint(32)
            if op_code == 0x7362d09c:
                cs.skip_bits(64)
                amount = cs.load_coins()
                sender = cs.load_address()
                jetton_wallet_address = tr.in_msg.info.src
                jetton_wallet_data = await get_wallet_data(client, jetton_wallet_address)
                jetton_data = await get_jetton_data(client, jetton_wallet_data['jetton_master_address'])
                print(f'JETTON TRANSFER {amount / 10**jetton_data.get("decimals", 9)} from {sender}')
                print(f'Balance: {jetton_wallet_data["balance"] / 10**jetton_data.get("decimals", 9)}')
                print(f'JETTON: {jetton_data["content"]}')


client = LiteBalancer.from_mainnet_config(trust_level=2)


async def main():
    await client.start_up()
    client.set_max_retries(3)
    scanner = BlockScanner(client=client, block_handler=handle_block)
    exc_num = 0
    while True:
        try:
            await scanner.run()
        except Exception as e:
            exc_num += 1
            print(e, type(e))
            if exc_num > 10:
                exc_num = 0
                await client.close_all()
                await asyncio.sleep(1)
                await client.start_up()
            continue


if __name__ == '__main__':
    asyncio.run(main())
