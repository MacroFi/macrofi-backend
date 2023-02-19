from src.user import user_profile_data, user_sex_enum
from src.usda_api import usda_nutrient_api
from src.server import macrofi_server
from src.recommendation_engine import recommendation_engine
import typing

def main():
    # create a test user
    user1 = user_profile_data(
        _uuid=1234, 
        _weight=170, 
        _height=69, 
        _age=20, 
        _sex=user_sex_enum.MALE, 
        _meals=[],
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
    
    # test recommendation engine
    user1_recommendation_engine = recommendation_engine(user=user1)
    print(f"[DEBUG] user_id='{user1._uuid}' calorie recommendation is {user1_recommendation_engine.calculate_calorie_need()}")
    
    # create test flask server
    server: macrofi_server = macrofi_server().init(in_memory_user_cache=user_cache, threaded=False)
    server.run()
    

if __name__ == "__main__":
    main()