from dataclasses import dataclass
import typing
import src.meal_definitions as meal_definitions


@dataclass
class user_profile_data:
    # unique identifier for the user
    _uuid: int 
    # weight of the user (in pounds)
    _weight: int
    # height of the user (in inches)
    _height: int
    # age of the user (in years)
    _age: int
    # list of meals associated with the user
    # TODO(Sean) read/write to cache
    _meals: typing.List[meal_definitions.meal_item]
    # TODO(Sean) personal goals
    # _personal_goals: typing.List[]
    # TODO(Sean) dietary restrictions
    # _dietary_restrictions: typing.List[]
    
    def __str__(self) -> str:
        new_line: str = "\n  "
        return f'''User(uuid={self._uuid}, weight={self._weight}, height={self._height}, age={self._age}):{new_line.join([str(meal) for meal in self._meals])}'''