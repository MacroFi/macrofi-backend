from dataclasses import dataclass
import typing
import src.meal_definitions as meal_definitions

class user_sex_enum:
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

@dataclass
class user_profile_data:
    # unique identifier for the user
    _uuid: int 
    # weight of the user (in pounds)
    _weight: float
    # height of the user (in inches)
    _height: int
    # age of the user (in years)
    _age: int
    # list of meals associated with the user
    # TODO(Sean) read/write to cache
    _meals: typing.List[meal_definitions.meal_item]
    # sex of the user
    _sex: str 
    # TODO(Sean) personal goals
    # _personal_goals: typing.List[]
    # TODO(Sean) dietary restrictions
    # _dietary_restrictions: typing.List[]
    
    def __str__(self) -> str:
        new_line: str = "\n  "
        return f'''User(uuid={self._uuid}, weight={self._weight} lb, height={self._height} in, age={self._age}, sex={self._sex}):{new_line.join([str(meal) for meal in self._meals])}'''
    
    """return the user's body weight in kilograms"""
    def get_body_weight_in_kg(self) -> float:
        return self._weight * 0.453592
    
    """return the user's height in cm"""
    def get_height_in_cm(self) -> float:
        return self._height * 2.54
    
    