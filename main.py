from src.user import user_profile_data, user_sex_enum
from src.usda_api import usda_nutrient_api
from src.yelp_api import yelp_api
from src.server import macrofi_server
from src.recommendation_engine import recommendation_engine
from src.meal_definitions import meal_item, food_item
import typing
import datetime
import argparse
import sys

# ======================
# command line arguments
# ======================
RUN_SERVER: bool = False
HEADLESS: bool = False
PORT: int = 5000
# ======================

def parse_cmd_line_arguments():
    global RUN_SERVER, HEADLESS, PORT
    
    parser = argparse.ArgumentParser(prog="macrofi-backend")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--server", action="store_true")
    parser.add_argument("-port", type=int, action="store")
    
    if len(sys.argv) > 1:
        args = vars(parser.parse_args())

        if args["headless"]:
            HEADLESS = True
        if args["server"]:
            RUN_SERVER = True
        if args["port"]:
            PORT = int(args["port"])   

def main():
    
    parse_cmd_line_arguments()
    
    # create a test meal
    test_meal1 = meal_item(_meal_name="test meal 1", _food_items=[food_item("test food 1", 500), food_item("test food 2", 450)], _time_eaten=datetime.datetime(2023, 2, 18, 9))
    test_meal2 = meal_item(_meal_name="test meal 2", _food_items=[food_item("test food 1", 850), food_item("test food 2", 600)], _time_eaten=datetime.datetime(2023, 2, 18, 12))
    test_meal3 = meal_item(_meal_name="test meal 3", _food_items=[food_item("test food 1", 200), food_item("test food 2", 400)], _time_eaten=datetime.datetime(2023, 2, 18, 4))
    test_meal4 = meal_item(_meal_name="test meal 4", _food_items=[food_item("test food 1", 500), food_item("test food 2", 450)], _time_eaten=datetime.datetime(2023, 2, 23, 9))
    test_meal5 = meal_item(_meal_name="test meal 5", _food_items=[food_item("test food 1", 850), food_item("test food 2", 600)], _time_eaten=datetime.datetime(2023, 2, 23, 12))
    test_meal6 = meal_item(_meal_name="test meal 6", _food_items=[food_item("test food 1", 200), food_item("test food 2", 400)], _time_eaten=datetime.datetime(2023, 2, 23, 4))
    # create a test user
    user1 = user_profile_data(
        _uuid=1234, 
        _weight=170, 
        _height=69, 
        _age=20, 
        _sex=user_sex_enum.MALE, 
        _meals=[test_meal1, test_meal2, test_meal3, test_meal4, test_meal5, test_meal6],
        _personal_goals=[],
        _dietary_restrictions=[]
    )
    print(user1)
    
    # create a test user cache
    user_cache: typing.Dict[int, user_profile_data] = { user1._uuid : user1  }
    
    # create a usda api wrapper object
    usda_api: usda_nutrient_api = usda_nutrient_api(headless=HEADLESS)
    # search for nutritional data using a keyword
    #usda_api.search_call("burger")
    #usda_api.search_call("fries")
    # search for nutritional data by uuid
    #usda_api.fetch_call(2353623)
    
    # create a yelp api wrapper object
    yelp: yelp_api = yelp_api(headless=HEADLESS)
    # search for nearby restaurants using keyword term and location
    #yelp.search_for_businesses(query_data={ "term":"delis", "location":"irvine" })
    
    # test recommendation engine
    user1_recommendation_engine = recommendation_engine(user=user1)
    print(f"[DEBUG] user_id='{user1._uuid}' calorie recommendation is {user1_recommendation_engine.calculate_calorie_need()}")
    user1_recommendation_engine.kmeans_clustering_on_meals()
    
    # create test flask server
    if RUN_SERVER:
        server: macrofi_server = macrofi_server().init(in_memory_user_cache=user_cache, headless=HEADLESS, threaded=False, port=PORT)
        server.run()
    

if __name__ == "__main__":
    main()