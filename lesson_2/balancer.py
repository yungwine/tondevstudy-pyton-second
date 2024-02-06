import asyncio

from pytoniq import LiteBalancer, LiteClientError, LiteServerError


async def main():
    client = LiteBalancer.from_testnet_config(trust_level=2)

    await client.start_up()

    try:
        print(await client.lookup_block(-1, -2**63, 100))
    except LiteServerError as e:
        print(e.code, e.message)

    await client.close_all()


if __name__ == '__main__':
    asyncio.run(main())
