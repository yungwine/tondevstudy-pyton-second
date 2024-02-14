import asyncio
import hashlib

from pytoniq import LiteBalancer
from pytoniq_core import Slice, begin_cell


def make_hash(key: str):
    return int.from_bytes(hashlib.sha256(key.encode()).digest(), 'big')


def get_keys():
    return {
        make_hash('name'): 'name',
        make_hash('description'): 'description',
        make_hash('image'): 'image',
        make_hash('image_data'): 'image_data',
        make_hash('symbol'): 'symbol',
        make_hash('decimals'): 'decimals'
    }


def parse_metadata(cs: Slice):
    if cs.remaining_bits < 8:
        return {}
    tag = cs.load_uint(8)
    if tag:
        return {'uri': cs.load_snake_string()}

    def key_deserializer(src):
        return get_keys().get(int(src, 2))

    def value_deserializer(src: Slice):
        src = src.load_ref().begin_parse()
        if src.preload_uint(8) == 0:
            src.skip_bits(8)
            return src.load_snake_string()
        return None

    return cs.load_dict(256, key_deserializer=key_deserializer, value_deserializer=value_deserializer)


async def get_jetton_data(client: LiteBalancer, jetton: str):
    result = await client.run_get_method(jetton, 'get_jetton_data', [])
    content = result[3]
    return {'total_supply': result[0], 'owner': result[2].load_address(), 'content': parse_metadata(content.begin_parse())}


async def get_wallet_address(client: LiteBalancer, jetton: str, owner_address: str):
    result = await client.run_get_method(jetton,
                                         'get_wallet_address',
                                         [begin_cell().store_address(owner_address).to_slice()]
                                         )
    return result[0].load_address()


async def get_wallet_data(client: LiteBalancer, address: str):
    result = await client.run_get_method(address, 'get_wallet_data', [])
    return {'balance': result[0], 'owner': result[1].load_address(), 'jetton_master_address': result[2].load_address()}


async def main():
    client = LiteBalancer.from_mainnet_config(trust_level=2)

    await client.start_up()

    # jetton_data = await get_jetton_data(client, 'EQBFYp-0MogncdEDf9b0vCdlkGvadbrMfaHSA_NrQ5PIXtnB')
    # print(jetton_data)
    jetton_wallet_address = await get_wallet_address(client, 'EQBFYp-0MogncdEDf9b0vCdlkGvadbrMfaHSA_NrQ5PIXtnB', 'EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c')
    print(jetton_wallet_address)

    jetton_wallet_data = await get_wallet_data(client, jetton_wallet_address)
    print(jetton_wallet_data)

    await client.close_all()


asyncio.run(main())
