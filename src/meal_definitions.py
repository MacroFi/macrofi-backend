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
    
    """serialize this object to json"""
    def to_json(self):
        # NOTE(Sean) after writing all the serializing code, I just realized that we could probably just use __dict__...
        as_json = dict()
        # serialize food item data
        as_json["food_name"] = self._food_name
        as_json["calories"] = self._calories
        as_json["nutrient_data"] = self._nutrient_data
        
        return as_json
    
    """create a food_item object from json"""
    @staticmethod
    def from_json(json_data):
        # get food name
        if json_data.get("food_name", None) is None:
            print("[SERVER] could not find food_name in food_item json!")
            assert False
        food_name: str = json_data["food_name"]
        
        # get calories
        if json_data.get("calories", None) is None:
            print("[SERVER] could not find food_name in calories json!")
            assert False
        calories: typing.Union[int, None] = None
        try:
            calories = int(json_data["calories"])
        except:
            print(f"""[SERVER] calorie data {json_data["calories"]} does not seem to be an integer""")
            assert False
        
        # get nutrient data
        if json_data.get("nutrient_data", None) is None:
            print("[SERVER] could not find food_name in nutrient_data json!")
            assert False
        nutrient_data = { key:float(value) for key,value in json_data["nutrient_data"].items() }
        
        return food_item(_food_name=food_name, _calories=calories, _nutrient_data=nutrient_data)

"""representation of a meal, which is a combination of individual food items"""
@dataclass
class meal_item:
    # name of the meal
    _meal_name: str = "DEFAULT_MEAL_NAME"
    # items in the meal
    _food_items: typing.List[food_item] = field(default_factory=list)
    # approximate time the meal was consumed
    _time_eaten: datetime.datetime = datetime.datetime.today()
    
    """serialize this object to json"""
    def to_json(self):
        # NOTE(Sean) after writing all the serializing code, I just realized that we could probably just use __dict__...
        as_json = dict()
        # serialize meal item data
        as_json["meal_name"] = self._meal_name
        as_json["food_items"] = [food.to_json() for food in self._food_items]
        as_json["time_eaten"] = str(self._time_eaten)
        
        return as_json
    
    """create a meal_item object from json"""
    @staticmethod
    def from_json(json_data):
        # get meal name
        meal_name: str = "DEFAULT_MEAL_NAME" if json_data.get("meal_name", None) is None else json_data["meal_name"]
        # get food items
        if json_data.get("food_items", None) is None:
            print("[SERVER] failed to retrive food_items from meal json!")
            assert False
        food_items: typing.List[food_item] = [food_item.from_json(food) for food in json_data["food_items"]]
        if json_data.get("time_eaten", None) is None:
            print("[SERVER] failed to retrive time_eaten from meal json!")
            assert False
        time_eaten = datetime.datetime.strptime(json_data["time_eaten"], "%Y-%m-%d %H:%M:%S")
        
        return meal_item(_meal_name=meal_name, _food_items=food_items, _time_eaten=time_eaten)
    
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