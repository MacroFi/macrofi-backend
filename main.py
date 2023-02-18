from src.user import user_profile_data
from src.usda_api import usda_nutrient_api

def main():
    # create a test user
    '''
    user1 = user_profile_data(_uuid=1234, _weight=120, _height=15, _age=20, _meals=[])
    print(user1)
    '''
    
    # create an api wrapper object
    usda_api: usda_nutrient_api = usda_nutrient_api()
    usda_api.search_call("burger")
    usda_api.fetch_call(2353623)
    

if __name__ == "__main__":
    main()