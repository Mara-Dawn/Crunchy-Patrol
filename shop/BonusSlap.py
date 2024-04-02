from datalayer.ItemTrigger import ItemTrigger
from shop.Item import Item
from shop.ItemGroup import ItemGroup
from shop.ItemType import ItemType

class BonusSlap(Item):

    def __init__(
        self,
        cost: int|None
    ):
        defaultcost = 35

        if cost is None:
            cost = defaultcost

        super().__init__(
            name = 'Bonus Slap',
            type = ItemType.BONUS_SLAP,
            group = ItemGroup.BONUS_ATTEMPT,
            description = 'Allows you to continue slapping a jailed person after using your guaranteed one.',
            emoji = '✋',
            cost = cost,
            value = True,
            view_class = None,
            allow_amount = False,
            base_amount = 1,
            max_amount = None,
            trigger = [ItemTrigger.SLAP]
        )