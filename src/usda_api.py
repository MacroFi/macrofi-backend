import os
import typing
import requests

import src.meal_definitions as meal_definitions

class usda_nutrient_api:
    
    # yeah yeah, plaintext bad
    USDA_API_KEY_FILE = "cs125_usda_api_key.txt"
    USDA_API_URL = "https://api.nal.usda.gov/fdc/v1"
    # token that we will replace with an actual food id when doing fetch
    USDA_API_FOOD_ID_TOKEN = "{fdcId}"
    # specific endpoints
    USDA_API_SEARCH_ENDPOINT = "/foods/search"
    USDA_API_FETCH_ENDPOINT = f"/food/{USDA_API_FOOD_ID_TOKEN}"
    
    TRACKED_NUTRIENTS = {
        "Energy" : "calories",
        "Protein" : "protein", 
        "Total lipid (fat)" : "fat", 
        "Carbohydrate, by difference": "carbohydrates", 
        "Sugars, total including NLEA" : "sugar"
    }
    
    
    def __init__(self, headless: bool = False):
        # flag for whether we are running headless
        self.__headless: bool = headless
        # internal list of valid api call types
        self.__api_call_types: typing.List[str] = ["fetch", "search"]
         
        # see if there is an api key, either read from file or ask user and store file.
        self.__api_key: typing.Union[str, None] = None
        try:
            with open(usda_nutrient_api.USDA_API_KEY_FILE, "r") as f:
                self.__api_key = f.read().strip()
        # TODO(Sean): propogate error if running in headless mode
        except OSError as err:
            print(f"[usda_api]: looks like there is no '{usda_nutrient_api.USDA_API_KEY_FILE}' file with an api key")
            
            # error when running headless
            if self.__headless:
                print(f"please create '{usda_nutrient_api.USDA_API_KEY_FILE}' with the api key and place in root directory.")
                exit(1)
                
            # ask user for key and store in file
            self.__api_key = input("[usda_api]: please enter an api key: ")
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
        
        # create request and payload
        url_with_key: str = self.__get_url_formatted("search")
        payload = {
            "query" : f"{food_item_name}",
            "sortBy" : "dataType.keyword",
            "pageSize" : "1"
        }
        
        print(f"[usda_api]: making SEARCH call to '{url_with_key}'")
        response = requests.get(url_with_key, params=payload)
        if not response:
            print("[usda_api]: SEARCH call failed!")
            return
        
        response_json = response.json()
        nutrients = {}
        if len(response_json["foods"]) > 0:
            foodNutrients = response_json["foods"][0]["foodNutrients"]

            for foodNutrient in foodNutrients:
                if foodNutrient["nutrientName"] in usda_nutrient_api.TRACKED_NUTRIENTS:
                    nutrients[usda_nutrient_api.TRACKED_NUTRIENTS[foodNutrient["nutrientName"]]] = foodNutrient["value"]

        return nutrients
    
    """helper function to search the USDA API for a food based on keyword, and return the best (currently first) result as a `food_item`"""
    def search_call_best_as_food_item(self, food_item_name: str):
        
        nutrients = self.search_call(food_item_name)
        calories = nutrients["calories"]
             
        return meal_definitions.food_item(_food_name=food_item_name, _calories=calories, _nutrient_data=nutrients)
        
    def fetch_call(self, food_id: int):
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
        
        url_with_key: str = self.__get_url_formatted("fetch").replace(usda_nutrient_api.USDA_API_FOOD_ID_TOKEN, str(food_id))
        
        print(f"[usda_api] :making FETCH call to '{url_with_key}'")
        response = requests.get(url_with_key)
        if not response:
            print("[usda_api]: FETCH call failed!")
            return
            
        response_json = response.json() 
        print(response_json)
        
        # TODO(Sean): parse/process before returning?
        return response_json