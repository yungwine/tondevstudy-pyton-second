import asyncio
import json

from pytoniq_core import Cell, StateInit, begin_cell, Address
from pytoniq import LiteClient, Contract, WalletV4R2

from secret import mnemo

boc = 'b5ee9c7241010c0100bd000114ff00f4a413f4bcf2c80b010201200302005af2d31fd33f31d31ff001f84212baf2e3e9f8000182107e8764efba9bd31f30f84201a0f862f002e030840ff2f0020148070402016e0605000db63ffe003f0850000db5473e003f08300202ce090800194f842f841c8cb1fcb1fc9ed5480201200b0a001d3b513434c7c07e1874c7c07e18b46000671b088831c02456f8007434c0cc1c6c244c383c0074c7f4cfcc4060841fa1d93beea6f4c7cc3e1080683e18bc00b80c2103fcbc208d1e30d3'

code = Cell.one_from_boc(boc)

data = begin_cell().store_uint(124, 32).store_uint(0, 32).end_cell()

state_init = StateInit(code=code, data=data)
state_init_cell = state_init.serialize()

# print(code)
# print(data)

addr = Address((0, state_init_cell.hash))

print(addr.to_str(is_bounceable=False))


async def external(contract):
    body = (begin_cell()
            .store_uint(0x7e8764ef, 32)
            .store_uint(0, 64)
            .store_uint(2, 32)
            .store_uint(5, 32)
            .end_cell())
    return await contract.send_external(state_init=state_init, body=body)


async def internal(wallet):
    body = begin_cell().store_uint(0x7e8764ef, 32).store_uint(0, 64).store_uint(1, 32).end_cell()
    await wallet.transfer(destination=addr, amount=5 * 10**7, body=body, state_init=state_init)


async def main():
    with open('../config.json', 'r') as f:
        config = json.loads(f.read())

    client = LiteClient.from_config(config, 0, trust_level=2)

    await client.connect()
    print(await client.get_masterchain_info())

    contract = await Contract.from_state_init(client, workchain=0, state_init=state_init)

    print(contract)
    wallet = await WalletV4R2.from_mnemonic(client, mnemo)
    print(wallet)

    result = await client.run_get_method(addr, 'get_counter', stack=[])
    print(result)


if __name__ == '__main__':
    asyncio.run(main())
