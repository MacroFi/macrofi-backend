import typing
import requests
import json
from collections import defaultdict

"""simple wrapper for yelp api calls"""
class yelp_api:
    
    # yeah yeah, plaintext bad
    YELP_API_KEY_FILE = "cs125_yelp_api_key.txt"
    
    YELP_API_URL = "https://api.yelp.com/v3"
    YELP_API_BUSINESS_SEARCH_ENDPOINT = "/businesses/search"
    # token for business id that will be replaced in search call
    BUSINESS_ID_TOKEN = "{id}"
    YELP_API_BUSINESS_DETAILS_ENDPOINT = f"/businesses/{BUSINESS_ID_TOKEN}"
    
    """internal method to get a formatted url for a specific api call"""
    def __init__(self, headless: bool = False):
        # flag for whether we are running headless
        self.__headless: bool = headless
        # valid options for api call
        self.__api_call_types: typing.List[str] = ["business_search", "business_details"]
        # see if there is an api key, either read from file or ask user and store file.
        self.__api_key: typing.Union[str, None] = None
        try:
            with open(yelp_api.YELP_API_KEY_FILE, "r") as f:
                self.__api_key = f.read().strip()
        except OSError as err:
            print(f"[yelp_api]: looks like there is no '{yelp_api.YELP_API_KEY_FILE}' file with an api key")
            
            # error when running headless
            if self.__headless:
                print(f"please create '{yelp_api.YELP_API_KEY_FILE}' with the api key and place in root directory.")
                exit(1)
            
            # ask user for key and store in file
            self.__api_key = input("[yelp_api]: please enter an api key: ")
            with open(yelp_api.YELP_API_KEY_FILE, "w") as f:
                f.write(self.__api_key)
    
    """internal method to get a formatted url for a specific api call"""
    def __get_url_formatted(self, api_call_type: str, **kwargs: typing.Dict[str, str]) -> str:
        # check for programmer error
        if api_call_type.lower() not in [call.lower() for call in self.__api_call_types]:
            assert False, f"{api_call_type} is not a valid option. valid_options=[{', '.join(call for call in self.__api_call_types)}]"
            
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
            
        # business search
        if api_call_type.lower() == self.__api_call_types[0].lower():
            return f"{yelp_api.YELP_API_URL}{yelp_api.YELP_API_BUSINESS_SEARCH_ENDPOINT}"
        # business details
        elif api_call_type.lower() == self.__api_call_types[1].lower():
            # generate url for REST call
            url = f"{yelp_api.YELP_API_URL}{yelp_api.YELP_API_BUSINESS_DETAILS_ENDPOINT}"
            # format 
            if kwargs.get("business_id", None) is None:
                assert False, f"__get_url_formatted(api_call_type={api_call_type}) requires business_id keyword arg"    
        
            return url.replace(yelp_api.BUSINESS_ID_TOKEN, kwargs["business_id"])
    
    """internal method to format the header authentication for yelp api calls"""
    def __get_auth_header(self) -> typing.Dict[str, str]:
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
            
        return { "Authorization" : f"Bearer {self.__api_key}" }
    
    
    """internal method to parse the json response from the yelp api calls"""
    def __search_for_businesses_parser(self, response: typing.Dict[str, list]):

        parsed_response = {"businesses" : []}
        
        for business in response.get("businesses", ""):
            parsed_business_info: typing.Dict[str, str] = {}
            
            parsed_business_info["name"]       = business.get("name", "")
            parsed_business_info["image_url"]  = business.get("image_url", "")
            parsed_business_info["phone"]      = business.get("phone", "") 
            parsed_business_info["address"]    = " ".join(business["location"]["display_address"])
            parsed_business_info["categories"] = [cat["title"] for cat in business.get("categories", [])]
            parsed_business_info["rating"]     = str(business.get("rating", ""))

            parsed_response["businesses"].append(parsed_business_info)

        return parsed_response
    
    """internal method to parse the json response from a business details get call."""
    def __business_details_parser(self, response: typing.Dict[str, str]) -> typing.Dict[str, str]:
        # TODO: processing
        return response
    
    """
    wrapper for a yelp business search, which will return results based on keywords, category, location, price, etc.
    query_data accepts the following data:
        "term" : str (keyword)
        "location": union[str, tuple[float, float]] (accepts either location string or (longitude, latitude))
    """
    def search_for_businesses(self, query_data: typing.Dict[str, str]):
        
        formatted_url: str = self.__get_url_formatted("business_search")
        header: typing.Dict[str, str] = self.__get_auth_header()
        
        # parse query data and add to request
        payload: typing.Dict[str, str] = dict()
        
        # term
        if query_data.get("term", None) is not None:
            payload["term"] = query_data['term']
        # location
        if query_data.get("location", None) is not None:
            loc_data = query_data["location"]
            if type(loc_data) is str:
                payload["location"] = loc_data
            elif type(loc_data) is tuple:
                payload["longitude"] = loc_data[0]
                payload["latitude"] = loc_data[1]
            else:
                assert False, f"location data must be a string or tuple(int, int)), but is {type(loc_data)}:'{loc_data}' "
        
        print(f"[yelp_api]: making business search GET call url='{formatted_url}', header='{header}'")
        try:
            response = requests.get(url=formatted_url, headers=header, params=payload)
        except:
            print(f"[yelp_api]: search_for_businesses(query_data={query_data}) failed to receive a response!")
        
        if response is None:
            print("[yelp_api]: business search GET call failed!")
            return {}
        
        print(response.json())
        
        return self.__search_for_businesses_parser(response.json())
    
    """wrapper for a yelp business details query, which will return rich business data for the passed in business id"""
    def get_rich_business_data_by_id(self, business_id: str):
        
        formatted_url: str = self.__get_url_formatted("business_details", business_id=business_id)
        print(f"[yelp_api]: get_rich_business_data_by_id(business_id={business_id}) url='{formatted_url}'")
        header: typing.Dict[str, str] = self.__get_auth_header()
        
        response = None
        try:
            response = requests.get(url=formatted_url, headers=header)
        except:
            print(f"[yelp_api]: get_rich_business_data_by_id(business_id={business_id}) failed to receive a response!")
        
        if response is None:
            print("[yelp_api]: business details GET call failed!")
            return {}
        
        return self.__business_details_parser(response.json())
        