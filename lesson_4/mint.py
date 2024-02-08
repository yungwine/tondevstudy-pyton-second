import asyncio

from pytoniq import LiteBalancer, Contract, WalletV4R2

from pytoniq_core import TlbScheme, Address, Cell, begin_cell, Slice, StateInit

from codes import collection_code, item_code
from secret import mnemo


class RoyaltyParams(TlbScheme):

    def __init__(self, royalty_factor: int, royalty_base: int, royalty_address: Address):
        self.royalty_factor = royalty_factor
        self.royalty_base = royalty_base
        self.royalty_address = royalty_address

    def serialize(self, *args) -> Cell:
        return begin_cell().store_uint(self.royalty_factor, 16).store_uint(self.royalty_base, 16).store_address(self.royalty_address).end_cell()

    @classmethod
    def deserialize(cls, cell_slice: Slice):
        return cls(cell_slice.load_uint(16), cell_slice.load_uint(16), cell_slice.load_address())


class NftCollectionData(TlbScheme):

    def __init__(self, owner_address: Address, next_item_index: int, content: Cell, nft_item_code: Cell, royalty_params: RoyaltyParams):
        self.owner_address = owner_address
        self.next_item_index = next_item_index
        self.content = content
        self.nft_item_code = nft_item_code
        self.royalty_params = royalty_params

    def serialize(self, *args):
        return begin_cell().store_address(self.owner_address).store_uint(self.next_item_index, 64).store_ref(self.content).store_ref(self.nft_item_code).store_ref(self.royalty_params.serialize()).end_cell()

    @classmethod
    def deserialize(cls, cell_slice: Slice):
        return cls(cell_slice.load_address(), cell_slice.load_uint(64), cell_slice.load_ref(), cell_slice.load_ref(), RoyaltyParams.deserialize(cell_slice.load_ref().begin_parse()))


async def get_collection(client: LiteBalancer):
    collection_metadata = (begin_cell()
                           .store_uint(1, 8)
                           .store_snake_string('https://s.getgems.io/nft-staging/c/628f6ab8077060a7a8d52d63/meta.json')
                           .end_cell())

    common_content = begin_cell().store_snake_string(
        'https://s.getgems.io/nft-staging/c/628f6ab8077060a7a8d52d63/').end_cell()

    content = begin_cell().store_ref(collection_metadata).store_ref(common_content).end_cell()

    data_cell = NftCollectionData(
        owner_address='UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9',
        next_item_index=0,
        content=content,
        nft_item_code=item_code,
        royalty_params=RoyaltyParams(0, 0, 'UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9')

    )

    state_init = StateInit(
        code=collection_code,
        data=data_cell.serialize()
    )
    return await Contract.from_state_init(client, 0, state_init=state_init)


async def get_wallet(client):
    return await WalletV4R2.from_mnemonic(client, mnemo)


async def deploy_collection(client: LiteBalancer, collection: Contract):
    collection = await get_collection(client)
    wallet = await get_wallet(client)

    await wallet.transfer(
        destination=collection.address,
        state_init=collection.state_init,
        amount=5 * 10 ** 7
    )


def get_nft_content_cell(index: int):
    return begin_cell().store_string(f'{index}.json').end_cell()


def get_mint_body(index: int, deploy_amount: int, owner: str):
    nft_content = begin_cell().store_address(owner).store_ref(get_nft_content_cell(index)).end_cell()
    return begin_cell().store_uint(index, 64).store_coins(deploy_amount).store_ref(nft_content).end_cell()


async def deploy_item(client: LiteBalancer):
    body = (begin_cell()
            .store_uint(1, 32)
            .store_uint(0, 64)
            .store_cell(get_mint_body(0, 2 * 10**7, 'UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9'))
            .end_cell())

    collection = await get_collection(client)
    wallet = await get_wallet(client)
    await wallet.transfer(
        destination=collection.address,
        amount=5 * 10 ** 7,
        body=body
    )


async def transfer(client: LiteBalancer):
    transfer_body = (begin_cell()
                     .store_uint(0x5fcc3d14, 32)
                     .store_uint(0, 64)
                     .store_address('UQCD39VS5jcptHL8vMjEXrzGaRcCVYto7HUn4bpAOg8xqEBI')
                     .store_address('UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9')
                     .store_bit_int(0)
                     .store_coins(0)
                     .store_bit_int(0)
                     .end_cell()
                     )
    wallet = await get_wallet(client)
    await wallet.transfer(
        destination='EQCaPYSKpeHO9bz4pjb1kvJFL8tOdp3Nir66Vd1BUMJzNBqX',
        amount=5 * 10 ** 7,
        body=transfer_body
    )


async def main():

    client = LiteBalancer.from_mainnet_config(trust_level=2)

    await client.start_up()

    await client.close_all()


asyncio.run(main())
