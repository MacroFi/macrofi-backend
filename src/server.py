import flask
from flask import Flask, jsonify, request
from flask_cors import CORS
import typing
from src.meal_definitions import meal_item, food_item
import src.user
import src.recommendation_engine as engine
from src.yelp_api import yelp_api
from src.usda_api import usda_nutrient_api
import datetime
import json
import threading
import time

# create flask app at a module level
flask_app = Flask(__name__) 
CORS(flask_app)

# simple singleton wrapper for a REST server, for sole use with the macrofi frontend app
class macrofi_server():
    
    DEFAULT_USER_PROFILE_FILE_NAME = "user_profile_data_cache.json"
    DEFAULT_MENU_ITEM_FILE_NAME = "menu_data_01.csv"
    
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
        self.__user_location_data_cache: typing.Dict[int, src.user.user_location_data] = {1234: src.user.user_location_data(uuid=1234, location="irvine", longitude=None, latitude=None)}
        # yelp api wrapper object
        self.__yelp_api: yelp_api = yelp_api(headless=self.__headless)
        # usda api wrapper object
        self.__usda_api: usda_nutrient_api = usda_nutrient_api(headless=self.__headless)
        # thread which periodically saves the user profile cache
        self.__user_profile_serialize_thread: typing.Union[threading.Thread, None] = None
        # cache of menu items from restaurant
        """
        schema:
        {
            cuisine: str : list[ { business_name: str : list[food_keyword: str] } ]
        }
        """
        self.__business_menu_item_cache: typing.Dict[str, typing.List[typing.Dict[str, typing.List[str]]]] = {}
        
        # deserialize business menu item data
        self.__deserialize_menu_data_from_file(filename=macrofi_server.DEFAULT_MENU_ITEM_FILE_NAME)
        
        # save to cache instantly if the user profile dictionary is pre-populated
        if self.__in_memory_user_cache:
            self.__serialize_user_profiles_to_file(macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME)
        
        # try loading serialized user profile data
        self.__deserialize_user_profiles_from_file(macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME)
        
        return self
    
    """initialize and run the flask server"""
    def run(self):
        print(f"[macrofi_server]: starting server on {self.__ip}:{self.__port}")
        # initialize a thread to periodically save our user profile cache
        self.__user_profile_serialize_thread = threading.Thread(target=self.__periodically_save_user_profile_cache_to_file)
        self.__user_profile_serialize_thread.daemon = True # so ctrl+c kills the thread
        self.__user_profile_serialize_thread.start()
        
        # TODO(Sean): figure out how to run out of debug mode
        flask_app.run(host=self.__ip, debug=True, threaded=self.__threaded, port=self.__port)
        
    """quit the flask server, and save any relevant data that is still in memory"""
    def quit(self):
        
        # stop any running threads
        if self.__user_profile_serialize_thread is not None:
            self.__user_profile_serialize_thread.join()
            
        # cache user profile data
        self.__serialize_user_profiles_to_file(macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME)
        
    """helper method to try convert uuid to int, gracefully fails"""
    def __uuid_as_int(self, uuid: str) -> typing.Union[int, None]:
        if type(uuid) is int:
            return uuid
        
        try:
            return int(uuid)
        except ValueError as err:
            print(f"uuid={uuid} is not a valid integer!")
            return None
    
    """internal method to check if the user is valid (stored in cache)"""
    def __is_valid_user(self, uuid: int) -> bool:
        if type(uuid) is str:
            uuid = int(uuid)
        return self.__in_memory_user_cache.get(uuid, None) is not None
    
    """internal method to get a user by id"""
    def __get_user(self, uuid: int) -> typing.Union[src.user.user_profile_data, None]:
        if type(uuid) is str:
            uuid = int(uuid)
        
        return self.__in_memory_user_cache.get(uuid, None)
    
    """internal method to serialize the in-memory user profiles to a file"""
    def __serialize_user_profiles_to_file(self, filename: typing.Union[str, None] = None) -> None:
        save_file_name: str = macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME if filename is None else filename
        print(f"[SERVER] serializing user profile data to '{save_file_name}'...")
        """open a file in write mode (will overwrite existing file), and dump the user profile cache as json"""
        with open(save_file_name, "w") as f:
            jsonified: typing.Dict[str, typing.Dict[str, str]] = { key:user.to_json() for key,user in self.__in_memory_user_cache.items() }
            json.dump(jsonified, f, indent=4)
        print(f"[SERVER] finished caching data.")
        
    """internal method to periodically save the user profile cache to a file"""
    def __periodically_save_user_profile_cache_to_file(self, wait_time: float = 300):
        # NOTE(Sean) this is not the "best" approach, but it works for an mvp
        time.sleep(wait_time)
        print("[SERVER] save user profile thread woke up!")
        # NOTE(Sean) due to python's GIL, we do not need any concurrent read/write protection
        self.__serialize_user_profiles_to_file(macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME)

    """internal method to deserialize user profile cache from json file."""
    def __deserialize_user_profiles_from_file(self, filename: typing.Union[str, None] = None) -> None:
        save_file_name: str = macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME if filename is None else filename
        """open a file in write mode (will overwrite existing file), and dump the user profile cache as json"""
        try:
            with open(save_file_name, "r") as f:
                deserialized_cache_json = json.load(f)
                deserialized_cache = { int(key) : src.user.user_profile_data.from_json(value) for key,value in deserialized_cache_json.items() }
                # set in memory user cache
                self.__in_memory_user_cache = deserialized_cache
        except OSError:
            print(f"[SERVER]: failed to find {save_file_name}.")
            
    """internal method to deserialize menu data and load into cache"""
    def __deserialize_menu_data_from_file(self, filename: typing.Union[str, None] = None):
        
        if filename is None:
            print(f"__deserialize_menu_data_from_file() did not specify a filename, defaulting to {macrofi_server.DEFAULT_MENU_ITEM_FILE_NAME}")
            filename = macrofi_server.DEFAULT_MENU_ITEM_FILE_NAME
        
        print("[SERVER]: starting to deserialize menu item cache...")
        with open(filename, "r") as f:
            data = f.readlines()
            
            for line in data:
                # strip spaces from beg or end of line and split on commas
                line_data = line.strip().split(',')
                # strip any spaces before or after data
                line_data = [d.strip() for d in line_data]
                
                assert len(line_data) > 3, f"invalid line={line_data}"
                
                cuisine_str = line_data[0]
                business_name = line_data[1]
                # get food menu items
                food_item_keywords = [line_data[i] for i in range(2, len(line_data))]
                
                business_dict = { business_name:food_item_keywords}
                
                # union between cached data and newly created data
                self.__business_menu_item_cache[cuisine_str] = self.__business_menu_item_cache.get(cuisine_str, {}) | business_dict
                
        print(self.__business_menu_item_cache)
        print("[SERVER]: finished to deserialize menu item cache")
                    
    
    """internal method to get meal data from a user, potentially specifying an earliest date for recorded meals"""
    def __get_user_meal_data(self, uuid: int, earliest_date: typing.Union[datetime.datetime, None] = None):
        if type(uuid) is str:
            uuid = int(uuid)

        if not self.__is_valid_user(uuid):
            assert False, f"invalid user_id={uuid}"
            
        found_user: src.user.user_profile_data = self.__get_user(uuid)
        
        if earliest_date is None:
            return found_user._meals
        else:
            return [meal for meal in found_user._meals if meal._time_eaten >= earliest_date]
    
    """internal method to return (or create) a recommendation engine for an active user"""
    def __get_or_create_recommendation_engine(self, uuid: int):
        assert self.__is_valid_user(uuid=uuid), "invalid user!"
        
        if self.__active_user_recommendation_engines.get(uuid, None) is None:
            print(f"[SERVER] recommendation engine for user_id={uuid} does not exist, creating...")
            self.__active_user_recommendation_engines[uuid] = engine.recommendation_engine(user=self.__get_user(uuid))
        
        return self.__active_user_recommendation_engines[uuid]
    
    """internal method to return today's date at 12:01am"""
    def __get_today_midnight(self):
        # get today's date at 12:01am
        today: datetime.datetime = datetime.datetime.today().replace(hour=0, minute=0, second=1)
        return today
    
    """internal method to add a meal to a specific user"""
    def __add_meal_to_user(self, uuid: int, meal: meal_item) -> None:
        assert self.__is_valid_user(uuid), "user is not valid?"
        self.__in_memory_user_cache[uuid]._meals.append(meal)
        self.__serialize_user_profiles_to_file(macrofi_server.DEFAULT_USER_PROFILE_FILE_NAME)
    
    # ===============================
    # flask endpoint helper functions
    # ===============================
    
    """internal method to check user cache and return a response"""
    def __flask_get_user_data(self, uuid: int):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
        print(f"[SERVER]: received GET get_user_data(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        found_user: typing.Union[None, src.user.user_profile_data] = self.__in_memory_user_cache.get(uuid, None)
        if found_user is None:
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        # TODO(Sean): return as json
        return jsonify(found_user)
    
    """internal method to get specific users meal from the cache and return a flask response"""
    def __flask_get_user_meal_data(self, uuid: int, earliest_date: typing.Union[datetime.datetime, None] = None):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
        print(f"[SERVER]: received GET get_user_meal_data(uuid={uuid})")
        
        if not self.__is_valid_user(uuid=uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        return jsonify({ "meals" : self.__get_user_meal_data(uuid=uuid, earliest_date=earliest_date) })
    
    def __flask_get_user_calorie_consumption_today(self, uuid: int):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
        print(f"[SERVER]: received GET __flask_get_user_calorie_today(uuid={uuid})")
        
        if not self.__is_valid_user(uuid=uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        meals: typing.List[meal_item] = self.__get_user_meal_data(uuid=uuid, earliest_date=self.__get_today_midnight())
        calories: float = sum(meal.get_total_calories() for meal in meals)
        
        return jsonify({ "calories" : calories })
    
    """internal method to get a specific user's daily calorie need (from the calculation)"""
    def __flask_get_user_calorie_calculation(self, uuid: int):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
        print(f"[SERVER]: received GET get_user_calorie_calculation(uuid={uuid})")
        if not self.__is_valid_user(uuid=uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)

        user_engine: engine.recommendation_engine = self.__get_or_create_recommendation_engine(uuid=uuid)
        
        return jsonify({ "calorie_need":user_engine.calculate_calorie_need() })
    
    def __flask_get_user_macronutrients(self, uuid: int):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
        print(f"[SERVER]: received GET get_user_calorie_calculation(uuid={uuid})")
        if not self.__is_valid_user(uuid=uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)

        user_engine: engine.recommendation_engine = self.__get_or_create_recommendation_engine(uuid=uuid)
        
        return jsonify({ "macronutrients":user_engine.calculate_macronutrients() })

    
    """internal method to get nearby restaurants from yelp api for a specific user"""
    def __flask_get_nearby_restaurants_for_user(self, uuid: int, term: str):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
        print(f"[SERVER]: received GET get_nearby_restaurants_for_user(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        if not self.__is_valid_user(uuid):
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=400)
        
        
        location_data: typing.Union[src.user.user_location_data, None] = self.__user_location_data_cache.get(uuid, None)
        print(self.__user_location_data_cache)
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
        
        if term != None:
            query_data["term"] = term
        
        return self.__yelp_api.search_for_businesses(query_data=query_data)
    
    """internal method to parse user data (as json) and store in cache"""
    def __flask_parse_user_data_json_and_cache(self, user_data_json):
        uuid: typing.Union[int, None] = user_data_json.get("uuid", None)
        if uuid is None:
            print(f"[SERVER] could not parse/find uuid in response!")
            return Flask.response(status=400)
        else:
            uuid = self.__uuid_as_int(uuid=uuid)
            if uuid is None:
                return flask.Response(status=400)
        
        # parse json
        weight: typing.Union[float, None] = user_data_json.get("weight", None)
        height: typing.Union[int, None] = user_data_json.get("height", None)
        age: typing.Union[int, None] = user_data_json.get("age", None)
        sex: typing.Union[str, None] = user_data_json.get("sex", None)
        goal: typing.Union[str, None] = user_data_json.get("goal", None) 
        dietary_restrictions: typing.Union[list[str], None] = user_data_json.get("dietary_restrictions", None)
        food_preferences: typing.Union[list[str], None] = user_data_json.get("food_preferences", None)
        
        if not self.__is_valid_user(uuid=uuid):
            # create new user
            print(f"[SERVER] creating new user uuid={uuid}!")
            new_user: src.user.user_profile_data = src.user.try_create_user_profile_data(int(uuid), float(weight), int(height), int(age), sex)
            self.__in_memory_user_cache[uuid] = new_user
        else:
            # update user profile data
            print(f"[SERVER] Updating profile data of user uuid={uuid}!")
            if weight is not None:
                self.__in_memory_user_cache[uuid]._weight = float(weight)
                
            if height is not None:
                self.__in_memory_user_cache[uuid]._height = int(height)
            
            if age is not None:
                self.__in_memory_user_cache[uuid]._age = int(age)
                
            if sex is not None:
                self.__in_memory_user_cache[uuid]._sex = sex
            
            if goal is not None:
                self.__in_memory_user_cache[uuid]._personal_goal = goal
            
            if dietary_restrictions is not None:
                self.__in_memory_user_cache[uuid]._dietary_restrictions = dietary_restrictions
            
            if food_preferences is not None:
                self.__in_memory_user_cache[uuid]._food_preferences = food_preferences

                
        return flask.Response(status=200)
    
    """internal method to store updated user location"""
    def __flask_put_user_location(self, uuid: int, location_json):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            return flask.Response(status=404)
        
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
    

    def __flask_get_meal_data(self, meal: typing.List[str]):
        print(f"[SERVER]: received POST __flask_get_meal_data(meal={meal})")

        meal_data = {}
        for food_item in meal:
            nutrients = self.__usda_api.search_call(food_item)
            meal_data[food_item] = nutrients

        return jsonify(meal_data)
    
    """
    internal method to cache a specific user's meal data
    json should be in the form { "meal_name":str (optional) "food_items": list[str] (food item keywords), "time_eaten": datetime (format: %Y-%m-%d %H:%M:%S) (optional) }
    """
    def __flask_put_user_meal_data(self, uuid: str, meal_data_json):
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            print("[SERVER] __flask_put_user_meal_data uuid is None!")
            return flask.Response(status=404)
        
        if not self.__is_valid_user(uuid):
            print("[SERVER] __flask_put_user_meal_data uuid is not valid (not found in user cache)!")
            return flask.Response(status=400)

        # parse meal name
        meal_name: typing.Union[str, None] = meal_data_json.get("meal_name", None)
        meal_name = "DEFAULT_MEAL_NAME"
        
        # parse time eaten
        time_eaten_str: typing.Union[str, None] = meal_data_json.get("time_eaten", None)
        time_eaten: typing.Union[datetime.datetime, None] = None
        if time_eaten_str is not None:
            time_eaten = datetime.datetime.strptime(time_eaten_str, "%Y-%m-%d %H:%M:%S")
        else:
            time_eaten = datetime.datetime.now()
        # check there are food items
        if meal_data_json.get("food_items", None) is None:
            print("[SERVER] __flask_put_user_meal_data food_items is not found!")
            return flask.Response(status=400)
        
        food_item_keywords: typing.List[str] = [keyword for keyword in meal_data_json["food_items"]]
        if not food_item_keywords:
            print("[SERVER] __flask_put_user_meal_data() food_items is empty!")
            return flask.Response(status=400)
        
        foods: typing.List[food_item] = []
        for keyword in food_item_keywords:
            food: food_item = self.__usda_api.search_call_best_as_food_item(keyword)
            assert type(food) is food_item, "bad return from api wrapper"
            foods.append(food)
        
        # create meal
        new_meal: meal_item = meal_item(_meal_name=meal_name, _food_items=foods, _time_eaten=time_eaten)
        
        print(f"[SERVER] PUT /v1/user/{uuid}/meals with payload='{meal_data_json}' created meal_item='{str(new_meal)}'")
        
        # add to user cache
        self.__add_meal_to_user(uuid, new_meal)
            
        return flask.Response(status=200)
    
    """internal method to call into recommendation engine for user, and get personalized recommendations"""
    def __flask_get_recommendations_for_user(self, uuid: int, n_recommendations: int = 10):
        # format uuid
        uuid = self.__uuid_as_int(uuid=uuid)
        if uuid is None:
            print("[SERVER] __flask_put_user_meal_data uuid is None!")
            return flask.Response(status=404)
        
        # assert the user is valid
        if not self.__is_valid_user(uuid):
            print("[SERVER] __flask_put_user_meal_data uuid is not valid (not found in user cache)!")
            return flask.Response(status=400)
        
        # try get cached location data
        location_data: typing.Union[src.user.user_location_data, None] = self.__user_location_data_cache.get(uuid, None)
        print(self.__user_location_data_cache)
        if location_data is None:
            print(f"[SERVER]: could not find location data for user_id={uuid} in __flask_get_recommendations_for_user(uuid={uuid}, n_recommendations={n_recommendations})")
            return flask.Response(status=400)
        
        # create user location payload for recommendation engine
        location_payload = None
        if location_data.has_location_string():
            location_payload = location_data.get_location_string()
        elif location_data.has_location_tuple():
            location_payload = location_data.get_location_tuple()
        else:
            assert False, "failed to parse and create location payload for find_n_recommendations!"
        
        return self.__get_or_create_recommendation_engine(
            uuid=uuid
        ).find_n_recommendations(
            n_recommendations=n_recommendations, 
            yelp_api=self.__yelp_api, 
            user_location=location_payload, 
            menu_item_cache=self.__business_menu_item_cache
        )
        
  
"""get, put, post api call for /v1/user/<uuid>"""
@flask_app.route("/v1/user/<uuid>", methods=["GET", "PUT", "POST"])
def update_user_data(uuid: int):
    if flask.request.method == "GET":
        return macrofi_server()._macrofi_server__flask_get_user_data(uuid=uuid)
    elif flask.request.method == "PUT" or flask.request.method == "POST":
        # parse json, check that data is valid, and cache
        return macrofi_server()._macrofi_server__flask_parse_user_data_json_and_cache(user_data_json=flask.request.get_json())
        
"""get, put api call for /v1/user/<uuid>/meals to cached meals from the specified user"""
@flask_app.route("/v1/user/<uuid>/meals", methods=["GET", "PUT"])
def get_user_meal_data(uuid: int):
    if flask.request.method == "GET":
        return macrofi_server()._macrofi_server__flask_get_user_meal_data(uuid=uuid)
    elif flask.request.method == "PUT":
        return macrofi_server()._macrofi_server__flask_put_user_meal_data(uuid=uuid, meal_data_json=flask.request.get_json())

"""get api call for /v1/user/<uuid>/meals/today to cached meals from the specified user, that were recorded from today's date"""
@flask_app.get("/v1/user/<uuid>/meals/today")
def get_user_meal_data_today(uuid: int):
    today: datetime.datetime = macrofi_server()._macrofi_server__get_today_midnight()
    return macrofi_server()._macrofi_server__flask_get_user_meal_data(uuid=uuid, earliest_date=today)

"""get api call for /v1/user/<uuid>/calorie/need"""
@flask_app.get("/v1/user/<uuid>/calorie/need")
def get_user_calorie_calculation(uuid: int):
    return macrofi_server()._macrofi_server__flask_get_user_calorie_calculation(uuid=uuid)

"""get api call for /v1/user/<uuid>/macros/need"""
@flask_app.get("/v1/user/<uuid>/macros")
def get_user_macros(uuid: int):
    return macrofi_server()._macrofi_server__flask_get_user_macronutrients(uuid=uuid)


"""get api call for /v1/user/<uuid>/calorie/today"""
@flask_app.get("/v1/user/<uuid>/calorie/today")
def get_user_calorie_consumption_today(uuid: int):
    return macrofi_server()._macrofi_server__flask_get_user_calorie_consumption_today(uuid=uuid)

"""get api call for /v1/user/<uuid>/nearby"""
@flask_app.get("/v1/user/<uuid>/nearby")
def get_nearby_restaurants_for_user(uuid: int):
    term = request.args.get("term", default=None)
    return macrofi_server()._macrofi_server__flask_get_nearby_restaurants_for_user(uuid=uuid, term=term)

"""get api call for /v1/user/<uuid>/recommendations"""
@flask_app.get("/v1/user/<uuid>/recommendations")
def get_recommendations_for_user(uuid: int):
    return macrofi_server()._macrofi_server__flask_get_recommendations_for_user(uuid=uuid, n_recommendations=10)

"""put api call for /v1/user/<uuid>/location"""
@flask_app.put("/v1/user/<uuid>/location")
def put_user_location(uuid: int):
    return macrofi_server()._macrofi_server__flask_put_user_location(
        uuid=uuid, 
        location_json=flask.request.get_json()
    )
    
"""get api call for /v1/today"""
@flask_app.get("/v1/today")
def get_today_midnight():
    return jsonify(macrofi_server()._macrofi_server__get_today_midnight())

"""get api call for /v1/meal_nutrients"""
@flask_app.get("/v1/meal_nutrients")
def get_meal_nutrients():
    meal = request.args.get("meal", default="").split(",")
    return macrofi_server()._macrofi_server__flask_get_meal_data(meal=meal)
