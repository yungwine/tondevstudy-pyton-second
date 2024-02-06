import asyncio
import json

from pytoniq import LiteBalancer, LiteClientError, LiteServerError, WalletV4R2
from pytoniq_core import begin_cell

from secret import mnemo


async def main():
    with open('../config.json', 'r') as f:
        config = json.loads(f.read())

    client = LiteBalancer.from_config(config, 2)

    await client.start_up()

    # wallet = await WalletV4R2.from_mnemonic(client, mnemo)
    # await wallet.transfer(
    #     'EQAufvUwaCtZ5j-SQvfmg8Ki2N5wc2g3yfFwdtGRa_1-RaGj',
    #     body=begin_cell().store_uint(1, 1).end_cell(),
    #     amount=2 * 10**7
    # )

    # trs = await client.get_transactions('EQAufvUwaCtZ5j-SQvfmg8Ki2N5wc2g3yfFwdtGRa_1-RaGj', 10)
    # tr = trs[0]
    # print(tr)
    # print(tr.description.compute_ph.exit_code)
    # trs = await client.get_transactions('UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9', 10)
    # tr = trs[0]
    # print(tr)
    # print(tr.in_msg.info.bounced)

    trs = await client.get_transactions('UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9', 10)

    tr = trs[2]
    cs = tr.in_msg.body.begin_parse()
    print(cs)

    op_code = cs.load_uint(32)

    if op_code == 0x7362d09c:
        cs.skip_bits(64)
        amount = cs.load_coins()
        sender = cs.load_address()
        print(amount, sender)

    await client.close_all()


if __name__ == '__main__':
    asyncio.run(main())
