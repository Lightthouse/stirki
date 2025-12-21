from enum import IntEnum


class OrderStates(IntEnum):
    INFO = 1

    # ask to reuse client settings - name, address
    REUSE_QUESTION = 777
    REUSE_CONFIRM = 111
    REUSE_REJECT = 222

    # client
    GET_PHONE = 2
    GET_NAME = 3
    GET_STREET = 4
    GET_HOUSE = 5
    GET_APARTMENT = 6
    GET_ENTRANCE = 7

    CLIENT_CONFIRM = 8

    # order options
    NEED_IRONING = 10
    NEED_CONDITIONER = 11
    NEED_VACUUM_PACK = 12
    NEED_UV = 13
    NEED_WASH_BAG = 14
    GET_COMMENT = 15

    CONFIRM = 20
    PAYMENT_QUESTION = 30
