from dataclasses import dataclass, field
import typing
import datetime


"""
representation of a "food", which is an individual unit of a meal. This is a generalized version of specific food items
for example: if a meal is an in-n-out burger and fries, then both the a general burger and general fries would be food items 
             in the meal.
"""
@dataclass
class food_item:
    # name of the food item
    _food_name: str
    # number of calories in the food
    _calories: int = 0
    # nutrients of the food
    _nutrient_data: typing.Dict[str, float] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"Food(name={self._food_name}, calories={self._calories})"

"""representation of a meal, which is a combination of individual food items"""
@dataclass
class meal_item:
    # name of the meal
    _meal_name: str
    # items in the meal
    _food_items: typing.List[food_item] = field(default_factory=list)
    # approximate time the meal was consumed
    _time_eaten: datetime.datetime = datetime.datetime.today()
    
    """return the total calorie count for the meal (sum the food items' calories)"""
    def get_total_calories(self) -> int:
        return sum([food._calories for food in self._food_items])
    
    """get all the nutrient data for the meal"""
    def get_total_nutrient_data(self) -> typing.Dict[str, float]:
        combined_nutrients: typing.Dict[str, float] = {}
        
        # iterate each food item's nutrient dict, and update the combined one
        for food in self._food_items:
            for nutrient, value in food._nutrient_data:
                
                # TODO(Sean): i think there is a more pythonic way to do this
                if combined_nutrients.get(nutrient) is not None:
                    combined_nutrients[nutrient] += value
                else:
                    combined_nutrients[nutrient] = value
            
        return combined_nutrients
    
    """get a string representation of the meal"""
    def __str__(self) -> str:
        return f"Meal(name={self._meal_name}, time_eaten={self._time_eaten}, food_items=[{','.join(str(food) for food in self._food_items)}])"