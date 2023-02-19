from src.user import user_profile_data
from src.usda_api import usda_nutrient_api
from src.server import macrofi_server
import typing

def main():
    
    # create a usda api wrapper object
    usda_api: usda_nutrient_api = usda_nutrient_api()
    #usda_api.search_call("burger")
    usda_api.fetch_call(2)
    
    # create a test user
    user1 = user_profile_data(_uuid=1234, _weight=120, _height=15, _age=20, _meals=[])
    print(user1)
    # create a test user cache
    user_cache: typing.Dict[int, user_profile_data] = { user1._uuid : user1  }
    
    # create test flask server
    server: macrofi_server = macrofi_server().init(in_memory_user_cache=user_cache, threaded=False)
    server.run()
    
    

if __name__ == "__main__":
    main()