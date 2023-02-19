from src.user import user_profile_data, user_sex_enum
from src.usda_api import usda_nutrient_api
from src.yelp_api import yelp_api
from src.server import macrofi_server
from src.recommendation_engine import recommendation_engine
from src.meal_definitions import meal_item, food_item
import typing
import datetime

# TODO: parse cmd line arguments and set
RUN_SERVER: bool = False

def main():
    
    # create a test meal
    test_meal1 = meal_item(_meal_name="test meal 1", _food_items=[food_item("test food 1", 500), food_item("test food 2", 450)], _time_eaten=datetime.datetime(2023, 2, 18, 9))
    test_meal2 = meal_item(_meal_name="test meal 2", _food_items=[food_item("test food 1", 850), food_item("test food 2", 600)], _time_eaten=datetime.datetime(2023, 2, 18, 12))
    test_meal3 = meal_item(_meal_name="test meal 3", _food_items=[food_item("test food 1", 200), food_item("test food 2", 400)], _time_eaten=datetime.datetime(2023, 2, 18, 4))
    # create a test user
    user1 = user_profile_data(
        _uuid=1234, 
        _weight=170, 
        _height=69, 
        _age=20, 
        _sex=user_sex_enum.MALE, 
        _meals=[test_meal1, test_meal2, test_meal3],
        _personal_goals=[],
        _dietary_restrictions=[]
    )
    print(user1)
    
    # create a test user cache
    user_cache: typing.Dict[int, user_profile_data] = { user1._uuid : user1  }
    
    # create a usda api wrapper object
    usda_api: usda_nutrient_api = usda_nutrient_api()
    #usda_api.search_call("burger")
    #usda_api.fetch_call(2353623)
    
    # create a yelp api wrapper object
    yelp: yelp_api = yelp_api()
    # yelp.search_for_businesses(query_data={ "term":"delis", "location":"irvine" })
    
    # test recommendation engine
    user1_recommendation_engine = recommendation_engine(user=user1)
    print(f"[DEBUG] user_id='{user1._uuid}' calorie recommendation is {user1_recommendation_engine.calculate_calorie_need()}")
    user1_recommendation_engine.kmeans_clustering_on_meals()
    
    # create test flask server
    if RUN_SERVER:
        server: macrofi_server = macrofi_server().init(in_memory_user_cache=user_cache, threaded=False)
        server.run()
    

if __name__ == "__main__":
    main()