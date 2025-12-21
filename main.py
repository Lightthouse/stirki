from src.services.kaiten_kanban import Kaiten
from src.enums import KaitenTagsNames, KaitenColumns
from icecream import ic

with Kaiten() as kc:
    description = (
        'Заказ #132 \n'
        '- Имя: Виктория Прутковская\n'
        '- Телефон: +7 (3452) 23-23-23\n'
        '- telegram id: 789234\n\n'
        '**Дополнительно:**\n'
        '1. Глажка  \n'
        '2. Мешок  \n'
    )

    card_id = 59086284

    tags = [
        {'name': KaitenTagsNames.IRONING},
        {'name': KaitenTagsNames.UV},
    ]
    change_card = kc.change_card_status(card_id, KaitenColumns.DRYING)
    # create_card = kc.create_card(title='From api 4222', description=description, tags=tags)
    # tags = kc.get_tags()
    # card = kc.get_card(create_card['id'])

    ic(change_card)