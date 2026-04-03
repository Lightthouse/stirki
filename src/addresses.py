STREETS = ['Рождественская', 'Новомытищинский проспект', 'Комарова', 'Воровского', 'Шараповский проезд']

STREETS_SLUG = {
    'Рождественская': 'rozhdestvenskaya',
    'Новомытищинский проспект': 'novomytishchinskay',
    'Комарова': 'komarova',
    'Воровского': 'vorovskogo',
    'Шараповский проезд': 'sharapovskaya',
}

HOUSE_STREET_MAP = {
    'Рождественская': ['11', '9', '7', '5', '3', '2'],
    'Новомытищинский проспект': ['4a'],
    'Комарова': ['2k1', '2k2', '2k3'],
    'Воровского': ['10'],
    'Шараповский проезд': ['вл2 ст3'],
}

# Числовые коды для QR-объявлений (ключ — число в ?ref=, значение — slug-адрес)
QR_CODE_MAP: dict[int, str] = {
    142: "rozhdestvenskaya-11",
    287: "rozhdestvenskaya-9",
    391: "rozhdestvenskaya-7",
    516: "rozhdestvenskaya-5",
    634: "rozhdestvenskaya-3",
    78:  "rozhdestvenskaya-2",
    203: "novomytishchinskay-4a",
    457: "komarova-2k1",
    819: "komarova-2k2",
    563: "komarova-2k3",
    721: "vorovskogo-10",
    345: "sharapovskaya-vl2-st3",
}
