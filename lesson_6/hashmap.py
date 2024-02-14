from pytoniq_core import HashMap, begin_cell, Address


def value_serializer(src, dest):
    if isinstance(src, int):
        return dest.store_int(src, 16)
    elif isinstance(src, str):
        return dest.store_int(int(src, 2), 16)
    raise Exception('unknown value type')


def key_serializer(src):
    if isinstance(src, int):
        return src
    elif isinstance(src, str):
        return len(src)


hm = HashMap(32, key_serializer=key_serializer, value_serializer=value_serializer)


hm.set(1, -10)
hm.set(2, -12)
hm.set(3, '100001')
hm.set('abcd', 100)


hashmap_cell = hm.serialize()

print(hashmap_cell)


def value_deserializer(src):
    return src.load_int(16)


print(HashMap.parse(hashmap_cell.begin_parse(), 32, value_deserializer=value_deserializer))


hashmap2 = HashMap(267).with_coins_values()

hashmap2.set(Address('UQCPCZU37-aComPLgaQBcOkevn4x5GJHSfZsFt6eF9DpHZH9'), 10**9)
hashmap2.set(Address('Ef9VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVbxn'), 500)

hashmap2_cell = hashmap2.serialize()


def value_deserializer2(src):
    return src.load_coins()


def key_deserializer2(src):
    return begin_cell().store_bits(src).to_slice().load_address()


print(HashMap.parse(hashmap2_cell.begin_parse(), 267, value_deserializer=value_deserializer2, key_deserializer=key_deserializer2))


cs = hashmap2_cell.begin_parse()

print(cs.load_hashmap(267, value_deserializer=value_deserializer2, key_deserializer=key_deserializer2))

new_cs = begin_cell().store_dict(hashmap2_cell).end_cell().begin_parse()
print(new_cs)

print(new_cs.load_dict(267))
