import asyncio
import requests

from pytoniq import LiteClient, LiteServerError


async def check_peer(client: LiteClient, seqno_from: int, seqno_to: int):
    seqno = (seqno_from + seqno_to) // 2

    if seqno_to - seqno_from <= 1:
        return seqno_to

    try:
        await client.lookup_block(-1, -2**63, seqno)
        print('exists: ', seqno)
        return await check_peer(client, seqno_from, seqno)

    except LiteServerError as e:
        if 'seqno not in db' in e.message:
            print('not exists: ', seqno)
            return await check_peer(client, seqno, seqno_to)
        print(e)

    except Exception as e:
        print(e)


async def main():
    config = requests.get('https://ton.org/testnet-global.config.json').json()

    for i in range(0, len(config['liteservers'])):

        client = LiteClient.from_config(config, ls_i=i, trust_level=2)
        await client.connect()
        last_seqno = client.last_mc_block.seqno
        print('last', last_seqno)

        oldest = await check_peer(client, 0, last_seqno)
        blk, block = await client.lookup_block(-1, -2 ** 63, oldest)
        print(f'PEER {i} KNOWS {oldest} GENERATED {block.info.gen_utime}')

        await client.close()


if __name__ == '__main__':
    asyncio.run(main())
