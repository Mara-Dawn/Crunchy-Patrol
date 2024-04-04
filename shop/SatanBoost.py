from datalayer.ItemTrigger import ItemTrigger
from shop.Item import Item
from shop.ItemGroup import ItemGroup
from shop.ItemType import ItemType
from view.ShopCategory import ShopCategory

class SatanBoost(Item):

    def __init__(
        self,
        cost: int|None
    ):
        defaultcost = 2345
        
        if cost is None:
            cost = defaultcost
            
        super().__init__(
            name = 'Satan\'s Nuclear Hellfart',
            type = ItemType.SATAN_FART,
            group = ItemGroup.VALUE_MODIFIER,
            shop_category = ShopCategory.FART,
            description = 'A x25 fart boost that sends a jailed person to the shadow realm but with a high risk of the farter being caught in the blast. 75% chance to jail yourself too with the same duration.',
            emoji = '😈',
            cost = cost,
            value = 25,
            view_class = None,
            allow_amount = False,
            base_amount = 1,
            max_amount = None,
            trigger = [ItemTrigger.FART]
        )