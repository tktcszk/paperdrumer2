


notes = {
    'c' : 1,
    'c_s': 2,
    'd' : 3,
    'd_s' : 4,
    'e' : 5,
    'f' : 6,
    'f_s' : 7,
    'g' : 8,
    'g_s' : 9,
    'a' : 10,
    'a_s' : 11,
    'b' : 12,
}

tonic = [
    [notes.c,       notes.e,            notes.g         ], # 1
    [               notes.e,            notes.g, notes.b], # 3
    [notes.c,       notes.e,                        notes.a         ], # 6
]

dominant = [
    [notes.g, notes.b, notes.d], # 5
    [notes.b, notes.d, notes.f] # 7
]

subdominant = [
    [notes.d, notes.f, notes.a], # 2
    [notes.f, notes.a, notes.c] # 4
]



