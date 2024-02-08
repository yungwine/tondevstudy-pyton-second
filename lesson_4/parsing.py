import asyncio

import requests
from pytoniq import LiteBalancer, Contract, WalletV4R2, RunGetMethodError

from pytoniq_core import TlbScheme, Address, Cell, begin_cell, Slice, StateInit


def parse_metadata(cs: Slice):
    if cs.preload_uint(8) == 1:
        cs.skip_bits(8)
        return requests.get(cs.load_snake_string()).json()


async def get_collection_data(client: LiteBalancer, address):
    data = await client.run_get_method(address=address, method='get_collection_data', stack=[])

    result = {
        'next_item_index': data[0],
        'metadata': parse_metadata(data[1].begin_parse()),
        'owner': data[2].load_address()
    }
    return result


async def get_nft_address_by_index(client: LiteBalancer, address, index: int):
    data = await client.run_get_method(address=address, method='get_nft_address_by_index', stack=[index])
    return data[0].load_address()


async def get_royalty_params(client: LiteBalancer, address: str):
    data = await client.run_get_method(address=address, method='royalty_params', stack=[])
    return {
        'royalty': data[0] / data[1] if data[1] != 0 else 0,
        'address': data[2].load_address()
    }


async def get_nft_data(client: LiteBalancer, address: str):
    data = await client.run_get_method(address=address, method='get_nft_data', stack=[])
    return {
        'init': data[0],
        'index': data[1],
        'collection_address': data[2].load_address(),
        'owner': data[3].load_address(),
        'content': data[4]
    }


async def get_nft_content(client: LiteBalancer, address: str, index: int, individual_nft_content: Cell):
    data = await client.run_get_method(address=address, method='get_nft_content',
                                       stack=[index, individual_nft_content])
    cs = data[0].begin_parse()
    cs.skip_bits(8)
    return cs.load_snake_string()


async def get_sale_data(client: LiteBalancer, address: str):
    data = await client.run_get_method(address=address, method='get_sale_data', stack=[])
    if data[0] == 0x46495850:
        return {
            'is_complete': data[1],
            'created_at': data[2],
            'marketplace_address': data[3].load_address(),
            'nft_address': data[4].load_address(),
            'nft_owner_address': data[5].load_address(),
            'full_price': data[6],
            'marketplace_fee_address': data[7].load_address(),
            'marketplace_fee': data[8],
            'royalty_address': data[9].load_address(),
            'royalty_amount': data[10]
        }
    elif data[0] == 0x415543:
        return {
            'is_complete': data[1],
            'end_time': data[2],
            'marketplace_address': data[3].load_address(),
            'nft_address': data[4].load_address(),
            'nft_owner_address': data[5].load_address(),
            'last_bid': data[6],
            'last_member': data[7].load_address(),
            'min_step': data[8],
            'marketplace_fee_address': data[9].load_address(),
            'marketplace_fee': data[10] / data[11] if data[11] != 0 else 0,
            'royalty_address': data[12].load_address(),
            'max_bid': data[15],
            'min_bid': data[16],
            'last_bid_at': data[18],
            'is_canceled': data[19]
        }


async def get_nft_on_sale(client: LiteBalancer, address: str):
    data = await get_nft_data(client, address)
    try:
        res = await get_sale_data(client, data['owner'])
        print('NFT is on sale')
        print('real owner: ', res['nft_owner_address'])
    except RunGetMethodError as e:
        print('NFT is not on sale')


async def main():

    collection_address = 'EQDyWZIoTXuEUaM6ROtnKs0lmtkJVWEg1vXMimm_A_rdMIyE'

    client = LiteBalancer.from_mainnet_config(trust_level=2)

    await client.start_up()

    col_data = await get_collection_data(client, collection_address)
    print(col_data)

    print(await get_nft_address_by_index(client, collection_address, 1))

    for i in range(0, col_data['next_item_index']):
        print(await get_nft_data(client, await get_nft_address_by_index(client, collection_address, i)))

    # print(await get_royalty_params(client, collection_address))
    #
    # data = await get_nft_data(client, 'EQCaPYSKpeHO9bz4pjb1kvJFL8tOdp3Nir66Vd1BUMJzNBqX')
    #
    # print(await get_nft_content(client, collection_address, 0, data['content']))
    #
    # print(await get_sale_data(client, 'EQDGFwA8KKTd12U5vI6gth3eJqyRpd3pTMT1Gm6eUGqDjI2_'))

    # await get_nft_on_sale(client, 'EQBo8Ukl3NoCOnBAedNNeSj7IutK7cj8PMllK3V4fKKjgJ1L')
    # await get_nft_on_sale(client, 'EQCaPYSKpeHO9bz4pjb1kvJFL8tOdp3Nir66Vd1BUMJzNBqX')

    await client.close_all()


asyncio.run(main())
