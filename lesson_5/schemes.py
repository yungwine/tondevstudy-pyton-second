from pytoniq_core import TlbScheme, Cell, Address, begin_cell, Slice, StateInit, HashMap


class JettonMinterData(TlbScheme):

    def __init__(self, total_supply: int, admin_address: Address, content: Cell, jetton_wallet_code: Cell):
        self.total_supply = total_supply
        self.admin_address = admin_address
        self.content = content
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self, *args):
        return begin_cell().store_coins(self.total_supply).store_address(self.admin_address).store_ref(self.content).store_ref(self.jetton_wallet_code).end_cell()

    @classmethod
    def deserialize(cls, cell_slice: Slice):
        return cls(cell_slice.load_coins(), cell_slice.load_address(), cell_slice.load_ref(), cell_slice.load_ref())


class JettonWalletData(TlbScheme):

    def __init__(self, balance: int, owner_address: Address, jetton_master_address: Address, jetton_wallet_code: Cell):
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self, *args):
        return begin_cell().store_coins(self.balance).store_address(self.owner_address).store_address(self.jetton_master_address).store_ref(self.jetton_wallet_code).end_cell()

    @classmethod
    def deserialize(cls, cell_slice: Slice):
        return cls(cell_slice.load_coins(), cell_slice.load_address(), cell_slice.load_address(), cell_slice.load_ref())
