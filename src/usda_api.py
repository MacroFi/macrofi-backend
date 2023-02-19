import os
import typing
import requests

class usda_nutrient_api:
    
    USDA_API_KEY_FILE = "cs125_usda_api_key.txt"
    USDA_API_URL = "https://api.nal.usda.gov/fdc/v1"
    # token that we will replace with an actual food id when doing fetch
    USDA_API_FOOD_ID_TOKEN = "{fdcId}"
    # specific endpoints
    USDA_API_SEARCH_ENDPOINT = "/foods/search"
    USDA_API_FETCH_ENDPOINT = f"/food/{USDA_API_FOOD_ID_TOKEN}"
    
    
    def __init__(self):
        
        # internal list of valid api call types
        self.__api_call_types: typing.List[str] = ["fetch", "search"]
        
        # see if there is an api key, either read from file or ask user and store file.
        self.__api_key: typing.Union[str, None] = None
        try:
            with open(usda_nutrient_api.USDA_API_KEY_FILE, "r") as f:
                self.__api_key = f.read().strip()
        # TODO(Sean): propogate error if running in headless mode
        except OSError as err:
            print(f"looks like there is no '{usda_nutrient_api.USDA_API_KEY_FILE}' file with an api key")
            # ask user for key and store in file
            self.__api_key = input("please enter an api key: ")
            with open(usda_nutrient_api.USDA_API_KEY_FILE, "w") as f:
                f.write(self.__api_key)
    
    """internal method to get a formatted url for a specific api call"""
    def __get_url_formatted(self, api_call_type: str):
        # check for programmer error
        if api_call_type.lower() not in [call.lower() for call in self.__api_call_types]:
            assert False, f"{api_call_type} is not a valid options. valid_options=[{', '.join(call for call in self.__api_call_types)}]"
            
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
            
        # fetch
        if api_call_type.lower() == self.__api_call_types[0].lower():
            return f"{usda_nutrient_api.USDA_API_URL}{usda_nutrient_api.USDA_API_FETCH_ENDPOINT}?api_key={self.__api_key}"
        # search
        elif api_call_type.lower() == self.__api_call_types[1].lower():
            return f"{usda_nutrient_api.USDA_API_URL}{usda_nutrient_api.USDA_API_SEARCH_ENDPOINT}?api_key={self.__api_key}"

    """perform a search api call on the usda nutrient database"""
    def search_call(self, food_item_name: str):
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
        
        url_with_key: str = self.__get_url_formatted("search")
        get_body = {
            "query" : f"{food_item_name}"
        }
        
        print(f"[DEBUG]: making usda nutrient api SEARCH call to '{url_with_key}'")
        response = requests.get(url_with_key, json=get_body)
        if not response:
            print("api SEARCH call failed!")
            return
        
        response_json = response.json() 
        print(response_json)
        
    def fetch_call(self, food_id: int):
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
        
        url_with_key: str = self.__get_url_formatted("fetch").replace(usda_nutrient_api.USDA_API_FOOD_ID_TOKEN, str(food_id))
        
        print(f"[DEBUG]: making usda nutrient api FETCH call to '{url_with_key}'")
        response = requests.get(url_with_key)
        if not response:
            print("api FETCH call failed!")
            return
            
        response_json = response.json() 
        print(response_json)