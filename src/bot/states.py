from enum import IntEnum


class OrderStates(IntEnum):
    INFO = 1

    # ask to reuse client settings - name, address
    REUSE_QUESTION = 2
    REUSE_CONFIRM = 3
    REUSE_REJECT = 4

    # client
    GET_PHONE = 5
    GET_NAME = 6
    GET_STREET = 7
    GET_HOUSE = 8
    GET_APARTMENT = 9
    GET_ENTRANCE = 10


    SELECT_SERVICES = 12

    # order options
    GET_COMMENT = 13

    CONFIRM = 14
    PAYMENT_QUESTION = 15
