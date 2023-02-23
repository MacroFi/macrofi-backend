from dataclasses import dataclass
import typing
import src.meal_definitions as meal_definitions
import datetime

class user_sex_enum:
    MALE: str = "male"
    FEMALE: str = "female"
    OTHER: str = "other"
    
class user_goal_enum:
    # TODO: other goals?
    WEIGHT_LOSS: str = "lose_weight"
    WEIGHT_GAIN: str = "gain_weight"
    BULK: str = "bulk"
    LEAN: str = "lean"

class user_dietary_restriction_enum:
    # TODO: other dietary restrictions
    VEGETARIAN: str = "vegetarian"
    VEGAN: str = "vegan"
    KETO: str = "keto"
    NO_GLUTEN: str = "no_gluten"
    NO_NUTS: str = "no_nuts"
    NO_FISH_OR_SHELLFISH: str = "no_fish_or_shellfish"
    NO_EGGS: str = "no_eggs"
    NO_SOY: str = "no_soy"
    
class user_preferences_enum:
    AMERICAN: str = "american"
    MEXICAN: str = "mexican"
    CHINESE: str = "chinese"
    INDIAN: str = "indian"
    THAI: str = "thai"

"""create a dietary restriction object (just a tuple with the type and a general "payload")"""
def create_dietary_restriction(type: user_dietary_restriction_enum, payload: str) -> typing.Tuple[user_dietary_restriction_enum, str]:
    return (type, payload)

@dataclass
class user_profile_data:
    # ================
    # public user data
    # ================
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
    # personal goals (used in recommendation engine)
    _personal_goals: typing.List[user_goal_enum]
    # dietary restrictions (used in recommendation engine)
    _dietary_restrictions: typing.List[typing.Tuple[user_dietary_restriction_enum, str]]
        
    def __str__(self) -> str:
        new_line: str = "\n  "
        return f'''User(uuid={self._uuid}, weight={self._weight} lb, height={self._height} in, age={self._age}, sex={self._sex}):{new_line if self._meals else ''}{new_line.join([str(meal) for meal in self._meals])}'''
    
    """return the user's body weight in kilograms"""
    def get_body_weight_in_kg(self) -> float:
        return self._weight * 0.453592
    
    """return the user's height in cm"""
    def get_height_in_cm(self) -> float:
        return self._height * 2.54
    
"""helper method to try create a user_profile_data object"""
def try_create_user_profile_data(
        uuid: int, weight: 
        typing.Union[float, None], 
        height: typing.Union[int, None], 
        age: typing.Union[int, None],
        sex: typing.Union[str, None]
    ) -> typing.Union[user_profile_data, None]:
    
    # check that we have valid data
    if uuid is None or type(uuid) is not int:
        print(f"[user_profile_data]: uuid is invalid")
        return None
    elif weight is None or type(weight) is not float:
        print(f"[user_profile_data]: weight is invalid")
        return None
    elif height is None or type(height) is not int:
        print(f"[user_profile_data]: height is invalid")
        return None
    elif age is None or type(age) is not int:
        print(f"[user_profile_data]: age is invalid!")
        return None
    elif sex is None or type(sex) is not str or sex not in [user_sex_enum.FEMALE, user_sex_enum.MALE, user_sex_enum.OTHER]:
        print(f"[user_profile_data]: sex is invalid!")
        return None
    
    # TODO: add meals, personal goals, dietary restrictions
    
    return user_profile_data(_uuid=uuid, _weight=weight, _height=height, _age=age, _meals=[], _sex=sex, _personal_goals=[], _dietary_restrictions=[])

"""struct to help record updates for a user's location"""
class user_location_data:
    def __init__(self, uuid: int, location: str, longitude: float, latitude: float, timestamp: typing.Union[datetime.datetime, None] = None):
        self.__uuid: int = uuid
        # location as a string keyword
        self.__location: str = location if location is not None else "ERR_NOT_PROVIDED"
        # location using specific longitude
        self.__longitude: typing.Union[float, None] = longitude
        # location using specific latitude
        self.__latitude: typing.Union[float, None] = latitude
        # current timestamp for recorded location
        self.__timestamp: datetime.datetime = datetime.datetime.today() if timestamp is None else timestamp
    
    """return the uuid associated with the location recording"""
    def get_uuid(self) -> int:
        return self.__uuid
    
    """return the location keyword"""
    def get_location_string(self) -> str:
        assert self.__location != "ERR_NOT_PROVIDED"
        return self.__location
    
    def has_location_string(self) -> bool:
        return self.__location != "ERR_NOT_PROVIDED"
    
    """return the longitude and latitude as a tuple"""
    def get_location_tuple(self) -> typing.Tuple[float, float]:
        assert self.__latitude is not None and self.__longitude is not None
        return (self.__longitude, self.__latitude)
    
    def has_location_tuple(self) -> bool:
        return self.__longitude is not None and self.__latitude is not None
    
    """get the longitude"""
    def get_longitude(self) -> float:
        assert self.__longitude is not None
        return self.__longitude
    
    """get the latitude"""
    def get_latitude(self) -> float:
        assert self.__latitude is not None
        return self.__latitude
    
    """get the timestamp for the location recording"""
    def get_timestamp(self) -> datetime.datetime:
        return self.__timestamp
    
    def __str__(self) -> str:
        return f"user_location_data(uuid={self.__uuid}, location={self.__location}, longitude={self.__longitude}, latitude={self.__latitude}, timestamp={self.__timestamp})"