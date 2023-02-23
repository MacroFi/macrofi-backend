import flask
from flask import Flask, jsonify
import typing
from src.meal_definitions import meal_item
import src.user
import src.recommendation_engine as engine
from src.yelp_api import yelp_api
from src.usda_api import usda_nutrient_api
import datetime

# create flask app at a module level
flask_app = Flask(__name__) 

# simple singleton wrapper for a REST server, for sole use with the macrofi frontend app
class macrofi_server():
    
    """singleton new constructor"""
    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(macrofi_server, self).__new__(self)
        
        return self.instance
    
    """initialize the instance"""
    def init(self, in_memory_user_cache: typing.Dict[int, src.user.user_profile_data], headless: bool = False, threaded: bool = False, port: int = 5000):
        # flag for whether the server is running headless
        self.__headless = headless
        # flag for whether we should run in threaded mode or not
        self.__threaded = threaded
        # port to run the server on
        self.__port = port
        # ip address to listen on
        self.__ip = "127.0.0.1"
        # user data in memory cache
        self.__in_memory_user_cache: typing.Dict[int, src.user.user_profile_data] = in_memory_user_cache
        # cache of active user recommendation engines
        self.__active_user_recommendation_engines: typing.Dict[int, engine.recommendation_engine] = { uuid : engine.recommendation_engine(user) for uuid, user in self.__in_memory_user_cache.items() }
        # cache of user's last posted location, used in the recommendation engine and for yelp's nearby restaurants
        # TODO(Sean): read/write to file
        self.__user_location_data_cache: typing.Dict[int, src.user.user_location_data] = {}
        # yelp api wrapper object
        self.__yelp_api: yelp_api = yelp_api(headless=self.__headless)
        # usda api wrapper object
        self.__usda_api: usda_nutrient_api = usda_nutrient_api(headless=self.__headless)
        
        return self
    
    """initialize and run the flask server"""
    def run(self):
        print(f"[macrofi_server]: starting server on {self.__ip}:{self.__port}")
        # TODO(Sean): figure out how to run out of debug mode
        flask_app.run(host=self.__ip, debug=True, threaded=self.__threaded, port=self.__port)
    
    """internal method to check if the user is valid (stored in cache)"""
    def __is_valid_user(self, uuid: int) -> bool:
        return self.__in_memory_user_cache.get(uuid, None) is not None
    
    """internal method to get a user by id"""
    def __get_user(self, uuid: int) -> typing.Union[src.user.user_profile_data, None]:
        return self.__in_memory_user_cache.get(uuid, None)
    
    """internal method to check user cache and return a response"""
    def __get_user_data(self, uuid: int):
        if type(uuid) is str:
            uuid = int(uuid)
        
        print(f"[SERVER]: received GET get_user_data(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        found_user: typing.Union[None, src.user.user_profile_data] = self.__in_memory_user_cache.get(uuid, None)
        if found_user is None:
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        # TODO(Sean): return as json
        return str(found_user)
    
    """internal method to return (or create) a recommendation engine for an active user"""
    def __get_or_create_recommendation_engine(self, uuid: int):
        assert self.__is_valid_user(uuid=uuid), "invalid user!"
        
        if self.__active_user_recommendation_engines.get(uuid, None) is None:
            print(f"[SERVER] recommendation engine for user_id={uuid} does not exist, creating...")
            self.__active_user_recommendation_engines[uuid] = engine.recommendation_engine(user=self.__get_user(uuid))
        
        return self.__active_user_recommendation_engines[uuid]
    
    """internal method to get specific users meal from the cache and return a response"""
    def __get_user_meal_data(self, uuid: int, earliest_date: typing.Union[datetime.datetime, None]):
        if type(uuid) is str:
            uuid = int(uuid)
        
        print(f"[SERVER]: received GET get_user_meal_data(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        found_user: typing.Union[None, src.user.user_profile_data] = self.__in_memory_user_cache.get(uuid, None)
        if found_user is None:
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        meals: typing.List[meal_item] = []
        if earliest_date is None:
            meals = found_user._meals
        else:
            meals = [meal for meal in found_user._meals if meal._time_eaten >= earliest_date]
        
        return jsonify({ "meals":meals })
    
    """internal method to get a specific user's daily calorie need (from the calculation)"""
    def __get_user_calorie_calculation(self, uuid: int):
        if type(uuid) is str:
            uuid = int(uuid)
        
        print(f"[SERVER]: received GET get_user_calorie_calculation(uuid={uuid})")
        if not self.__is_valid_user(uuid=uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)

        user_engine: engine.recommendation_engine = self.__get_or_create_recommendation_engine(uuid=uuid)
        
        return jsonify({ "calorie_need":user_engine.calculate_calorie_need() })
    
    """internal method to get nearby restaurants from yelp api for a specific user"""
    def __get_nearby_restaurants_for_user(self, uuid: int):
        if type(uuid) is str:
            uuid = int(uuid)
        
        print(f"[SERVER]: received GET get_nearby_restaurants_for_user(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        if not self.__is_valid_user(uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        
        location_data: typing.Union[src.user.user_location_data, None] = self.__user_location_data_cache.get(uuid, None)
        if location_data is None:
            print(f"[SERVER]: could not find location data for user_id={uuid}")
            return flask.Response(status=400)
        
        # TODO: hook into recommendation engine and do actual recommendations
        
        # form correct query data for yelp api call, using cached location data
        query_data: typing.Dict[str, str] = {}
        if location_data.has_location_string():
            query_data["location"] = location_data.get_location_string()
        elif location_data.has_location_tuple():
            query_data["longitude"] = location_data.get_longitude()
            query_data["latitude"] = location_data.get_latitude()
        else:
            print(f"[SERVER] cached location data '{location_data}' is invalid!")
            return Flask.response(status=404)
        
        # TODO(Sean): add keyword term to search
        
        return self.__yelp_api.search_for_businesses(query_data=query_data)
    
    """internal method to parse user data (as json) and store in cache"""
    def __parse_user_data_json_and_cache(self, user_data_json):
        
        uuid: typing.Union[int, None] = user_data_json.get("uuid", None)
        if uuid is None:
            print(f"[SERVER] could not parse/find uuid in response!")
            return Flask.response(status=400)
        else:
            uuid = int(uuid)
        
        # parse json
        weight: typing.Union[float, None] = user_data_json.get("weight", None)
        height: typing.Union[int, None] = user_data_json.get("height", None)
        age: typing.Union[int, None] = user_data_json.get("age", None)
        sex: typing.Union[str, None] = user_data_json.get("sex", None)
        
        # TODO(Sean): parse meals, goals, and preferences
        
        if not self.__is_valid_user(uuid=uuid):
            # create new user
            new_user: src.user.user_profile_data = src.user.try_create_user_profile_data(int(uuid), float(weight), int(height), int(age), sex)
            self.__in_memory_user_cache[uuid] = new_user
        else:
            # update user profile data
            if weight is not None:
                self.__in_memory_user_cache[uuid]._weight = float(weight)
                
            if height is not None:
                self.__in_memory_user_cache[uuid]._height = int(height)
            
            if age is not None:
                self.__in_memory_user_cache[uuid]._age = int(age)
                
            if sex is not None:
                self.__in_memory_user_cache[uuid]._sex = sex
                
        return flask.Response(status=200)
    
    """internal method to store updated user location"""
    def __put_user_location(self, uuid: int, location_json):
        # check for valid user
        if not self.__is_valid_user(uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)

        # parse json object
        location_str: typing.Union[str, None] = location_json.get("location", None)
        longitude: typing.Union[str, None] = location_json.get("longitude", None)
        latitude: typing.Union[str, None] = location_json.get("latitude", None)
        
        # assert we received one form of location (keyword or longitude/latitude pair)
        if location_str is None and (longitude is None or latitude is None):
            print(f"[SERVER] location json is invalid '{location_json}'")
            return flask.Response(400) 
        
        # TODO(Sean): actually parse location from json
        location_data: src.user.user_location_data = src.user.user_location_data(
            uuid=uuid, 
            location=location_str, 
            longitude=longitude, 
            latitude=latitude
        )
        
        # store in cache
        self.__user_location_data_cache[uuid] = location_data
        
        print(f"[SERVER] stored {str(location_data)}")
        
        return flask.Response(status=200)
        
"""get, put, post api call for /v1/user/<uuid>"""
@flask_app.route("/v1/user/<uuid>", methods=["GET", "PUT", "POST"])
def update_user_data(uuid: int):
    if flask.request.method == "GET":
        return macrofi_server()._macrofi_server__get_user_data(uuid=uuid)
    elif flask.request.method == "PUT" or flask.request.method == "POST":
        # parse json, check that data is valid, and cache
        return macrofi_server()._macrofi_server__parse_user_data_json_and_cache(user_data_json=flask.request.get_json())
        
"""get api call for /v1/user/<uuid>/meals to cached meals from the specified user"""
@flask_app.get("/v1/user/<uuid>/meals")
def get_user_meal_data(uuid: int):
    return macrofi_server()._macrofi_server__get_user_meal_data(uuid=uuid)

"""get api call for /v1/user/<uuid>/meals/today to cached meals from the specified user, that were recorded from today's date"""
@flask_app.get("/v1/user/<uuid>/meals/today")
def get_user_meal_data_today(uuid: int):
    # get today's date at 12:01am
    today: datetime.datetime = datetime.date.today()
    today.hour = 0
    today.minute = 1
    
    return macrofi_server()._macrofi_server__get_user_meal_data(uuid=uuid, earliest_date=today)

"""get api call for /v1/user/<uuid>/calorie_need"""
@flask_app.get("/v1/user/<uuid>/calorie_need")
def get_user_calorie_calculation(uuid: int):
    return macrofi_server()._macrofi_server__get_user_calorie_calculation(uuid=uuid)

"""get api call for /v1/user/nearby/<uuid>"""
@flask_app.get("/v1/user/<uuid>/nearby")
def get_nearby_restaurants_for_user(uuid: int):
    return macrofi_server()._macrofi_server__get_nearby_restaurants_for_user(uuid=uuid)

"""put api call for /v1/user/location/<uuid>"""
@flask_app.put("/v1/user/<uuid>/location")
def put_user_location(uuid: int):
    return macrofi_server()._macrofi_server__put_user_location(
        uuid=uuid, 
        location_json=flask.request.get_json()
    )
