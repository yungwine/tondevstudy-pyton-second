from pytoniq_core import Builder, Cell, Slice, begin_cell, Address


b = begin_cell().store_uint(15, 32)

b.store_address('EQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHcw4')

c = b.end_cell()

c2 = begin_cell().store_uint(1, 1).store_ref(c).end_cell()

print([c2])

s = c2.begin_parse()

print(s)
print(s.load_uint(1))
new_c = s.load_ref()

new_s = new_c.begin_parse()

print(new_s.load_uint(32))

addr = new_s.load_address()
print(addr)

print(Address('EQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHcw4').to_str(is_user_friendly=False))
