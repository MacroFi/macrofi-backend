import requests
import typing

"""
wrapper for uber eats api
NOTE: this is not finished because we do not have api access yet.
"""
class uber_eats_api:
    
    UBER_API_KEY_FILE = "cs125_uber_eats_api_key.txt"
    # root url for api
    UBER_API_URL = "https://api.uber.com/v2"
    # token for store id that can be substring replaced
    UBER_API_GET_MENU_STORE_ID_TOKEN = "{store_id}"
    # menu endpoint
    UBER_API_GET_MENU_ENDPOINT = f"/eats/stores/{UBER_API_GET_MENU_STORE_ID_TOKEN}/menus"
    
    def __init__(self, headless: bool = False):
        # flag for whether we are running headless
        self.__headless: bool = headless
        # valid options for api call
        self.__api_call_types: typing.List[str] = []
        # see if there is an api key, either read from file or ask user and store file.
        self.__api_key: typing.Union[str, None] = None
        try:
            with open(uber_eats_api.UBER_API_KEY_FILE, "r") as f:
                self.__api_key = f.read().strip()
        except OSError as err:
            print(f"[uber_eats_api]: looks like there is no '{uber_eats_api.UBER_API_KEY_FILE}' file with an api key")
            
            # error when running headless
            if self.__headless:
                print(f"please create '{uber_eats_api.UBER_API_KEY_FILE}' with the api key and place in root directory.")
                exit(1)
            
            # ask user for key and store in file
            self.__api_key = input("[uber_eats_api]: please enter an api key: ")
            with open(uber_eats_api.UBER_API_KEY_FILE, "w") as f:
                f.write(self.__api_key)