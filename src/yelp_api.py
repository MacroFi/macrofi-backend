import typing
import requests

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
    def __get_url_formatted(self, api_call_type: str) -> str:
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
            return f"{yelp_api.YELP_API_URL}{yelp_api.YELP_API_BUSINESS_DETAILS_ENDPOINT}"
    
    """internal method to format the header authentication for yelp api calls"""
    def __get_auth_header(self) -> typing.Dict[str, str]:
        # check for programmer error
        if self.__api_key is None:
            assert False, "api key not set!"
            
        return { "Authorization" : f"Bearer {self.__api_key}" }
        
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
        query_params: typing.List[str] = []
        
        # term
        if query_data.get("term", None) is not None:
            query_params.append(f"term={query_data['term']}")
        # location
        if query_data.get("location", None) is not None:
            loc_data = query_data["location"]
            if type(loc_data) is str:
                query_params.append(f"location={loc_data}")
            elif type(loc_data) is tuple:
                query_params.append(f"longitude={loc_data[0]}")
                query_params.append(f"latitude={loc_data[1]}")
            else:
                assert False, "location data must be a string or tuple(int, int))!"
            
        # append query params to url
        if query_params:
            formatted_url += f"?{'&'.join([param for param in query_params])}"
        
        
        print(f"[yelp_api]: making business search GET call url='{formatted_url}', header='{header}'")
        response = requests.get(url=formatted_url, headers=header)
        if response is None:
            print("[yelp_api]: business search GET call failed!")
        
        print(response.json())
        
        # TODO(Sean): parse/process before returning?
        return response.json()