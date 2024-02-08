import asyncio
import json
import time

from pytoniq import LiteBalancer, BlockIdExt


async def main():
    with open('../config.json', 'r') as f:
        config = json.loads(f.read())

    client = LiteBalancer.from_config(config, 2)

    await client.start_up()

    m_info = await client.get_masterchain_info()
    print(m_info)

    blk, _ = await client.lookup_block(-1, -2**63, m_info['last']['seqno'])
    print(blk)

    # blk, _ = await client.lookup_block(0, -4611686018427387904, utime=int(time.time()) - 100)
    # print(blk)

    # block = await client.raw_get_block_header(blk)
    # print(block)
    # block = await client.raw_get_block(blk)
    # print(block)
    # trs = await client.raw_get_block_transactions(blk)
    # print(trs)
    # print(await client.get_transactions(address=trs[0]['account'], count=1, from_hash=trs[0]['hash'], from_lt=trs[0]['lt']))
    # trs = await client.raw_get_block_transactions_ext(blk)
    # print(trs)

    # shards = await client.get_all_shards_info(blk)
    # print(shards)

    print(await client.get_config_params([28]))


    await client.close_all()


asyncio.run(main())
