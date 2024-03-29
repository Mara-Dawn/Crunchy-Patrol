from shop.IsntantItem import InstantItem
from shop.ItemGroup import ItemGroup
from shop.ItemType import ItemType
class Arrest(InstantItem):

    def __init__(
        self,
        cost: int|None
    ):
        self.name = 'Citizens Arrest'
        type = ItemType.ARREST
        group = ItemGroup.IMMEDIATE_USE
        self.description = 'Take the law into your own hands and arrest a user of choice for 30 minutes.'
        defaultcost = 1000
        emoji = '🚨'
        view = 'ShopUserSelectView'
        value = None
        
        if cost is None:
            cost = defaultcost
        
        super().__init__(self.name, type, group, self.description, emoji, cost, view, value)