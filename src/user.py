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
    _personal_goal: user_goal_enum
    # dietary restrictions (used in recommendation engine)
    _dietary_restrictions: typing.List[user_dietary_restriction_enum]

    _food_preferences: typing.List[user_preferences_enum]
        
    def __str__(self) -> str:
        new_line: str = "\n  "
        return f'''User(uuid={self._uuid}, weight={self._weight} lb, height={self._height} in, age={self._age}, sex={self._sex}):{new_line if self._meals else ''}{new_line.join([str(meal) for meal in self._meals])}'''
    
    """return the user's body weight in kilograms"""
    def get_body_weight_in_kg(self) -> float:
        return self._weight * 0.453592
    
    """return the user's height in cm"""
    def get_height_in_cm(self) -> float:
        return self._height * 2.54
    
    """return this object as json"""
    def to_json(self):
        as_json = dict()
        # serialize data
        as_json["uuid"] = str(self._uuid)
        as_json["weight"] = str(self._weight)
        as_json["height"] = str(self._height)
        as_json["age"] = str(self._age)
        as_json["meals"] = [meal.to_json() for meal in self._meals]
        as_json["sex"] = str(self._sex)
        as_json["food_preferences"] = self._food_preferences
        as_json["dietary_restrictions"] = self._dietary_restrictions
        as_json["personal_goals"] = self._personal_goal
        
        return as_json
    
    @staticmethod
    def from_json(json_data):
        # NOTE(Sean) this is not very beautiful code, but fine for an mvp
        # NOTE(Sean) after writing all the serializing code, I just realized that we could probably just use __dict__...
        
        # get uuid
        uuid: typing.Union[int, None] = None
        if json_data.get("uuid", None) is None:
            print("[SERVER]: failed to find uuid, which is necessary to construct a user.")
            assert False, "failed to find uuid"
        try:
            uuid = int(json_data["uuid"])
        except:
            print(f"[SERVER]: uuid '{uuid}' does not seem to be an integer")
            assert False, "failed to format uuid"
        
        # get weight data
        weight: typing.Union[float, None] = None
        if json_data.get("weight", None) is None:
            print("[SERVER]: failed to find uuid, which is necessary to construct a user.")
            assert False, "failed to find uuid"
        try:
            weight = float(json_data["weight"])
        except:
            print(f"[SERVER]: weight '{weight}' does not seem to be an float")
            assert False, "failed to format weight"
            
        # get height data
        height: typing.Union[int, None] = None
        if json_data.get("height", None) is None:
            print("[SERVER]: failed to find height, which is necessary to construct a user.")
            assert False, "failed to find height"
        try:
            height = int(json_data["height"])
        except:
            print(f"[SERVER]: height '{height}' does not seem to be an int")
            assert False, "failed to format height"
            
        # get age data
        age: typing.Union[int, None] = None
        if json_data.get("age", None) is None:
            print("[SERVER]: failed to find age, which is necessary to construct a user.")
            assert False, "failed to find age"
        try:
            age = int(json_data["age"])
        except:
            print(f"[SERVER]: age '{age}' does not seem to be an int")
            assert False, "failed to format age"
            
        # get sex data
        sex: typing.Union[str, None] = None
        if json_data.get("sex", None) is None:
            print("[SERVER]: failed to find sex, which is necessary to construct a user.")
            assert False, "failed to find sex"
        sex = json_data["sex"]
            
        # get meal data
        if json_data.get("meals", None) is None:
            print("[SERVER]: failed to find meals, which is necessary to construct a user.")
            assert False, "failed to find meals"
        
        meal_list_json = json_data["meals"]
        meal_data = [meal_definitions.meal_item.from_json(meal) for meal in meal_list_json]
            
        # get food preference data
        if json_data.get("food_preferences", None) is None:
            print("[SERVER]: failed to find food_preferences, which is necessary to construct a user.")
            assert False, "failed to find food_preferences"
        
        food_preferences = [pref for pref in json_data["food_preferences"]]
        
        # get dietary restriction data
        if json_data.get("dietary_restrictions", None) is None:
            print("[SERVER]: failed to find dietary_restrictions, which is necessary to construct a user.")
            assert False, "failed to find dietary_restrictions"
        
        dietary_restrictions = [restr for restr in json_data["dietary_restrictions"]]
        
        # get personal goal data
        if json_data.get("personal_goals", None) is None:
            print("[SERVER]: failed to find personal_goals, which is necessary to construct a user.")
            assert False, "failed to find personal_goals"
        
        personal_goals = [goal for goal in json_data["personal_goals"]]
        
        user = user_profile_data(
            _uuid=uuid,
            _weight=weight,
            _height=height,
            _age=age,
            _meals=meal_data,
            _sex=sex,
            _personal_goal=personal_goals,
            _dietary_restrictions=dietary_restrictions,
            _food_preferences=food_preferences
        )
        
        return user
        
        
            
        
    
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
    
    return user_profile_data(_uuid=uuid, _weight=weight, _height=height, _age=age, _meals=[], _sex=sex, _personal_goal="", _dietary_restrictions=[], _food_preferences=[])

"""struct to help record updates for a user's location"""
class user_location_data:
    def __init__(self, uuid: int, location: str, longitude: float, latitude: float, timestamp: typing.Union[datetime.datetime, None] = None):
        self.__uuid: int = uuid
        # location as a string keyword
        self.__location: str = location if location is not None else "ERR_NOT_PROVIDED"
        # location using specific longitude
        self.__longitude: typing.Union[float, None] = float(longitude) if longitude is not None else None
        # location using specific latitude
        self.__latitude: typing.Union[float, None] = float(latitude) if latitude is not None else None
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