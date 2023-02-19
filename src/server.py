import flask
from flask import Flask
import typing
import src.user

# create flask app at a module level
flask_app = Flask(__name__) 

# simple singleton wrapper for a REST server, for sole use with the macrofi frontend app
class macrofi_server():
    
    """singleton new constructor"""
    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(macrofi_server, self).__new__(self)
        
        return self.instance
    
    """initialize the instance"""
    def init(self, in_memory_user_cache: typing.Dict[int, src.user.user_profile_data], threaded: bool = False):
        # flag for whether we should run in threaded mode or not
        self.__threaded = threaded
        # user data in memory cache
        self.__in_memory_user_cache: typing.Dict[int, src.user.user_profile_data] = in_memory_user_cache
        
        return self
    
    """initialize and run the flask server"""
    def run(self):
        # TODO(Sean): figure out how to run out of debug mode
        flask_app.run(host="0.0.0.0", debug=True, threaded=self.__threaded)
    
    """internal method to check user cache and return a response"""
    def __get_user_data(self, uuid: int):
        if type(uuid) is str:
            uuid = int(uuid)
        
        print(f"[SERVER]: received GET get_user_data(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        found_user: typing.Union[None, src.user.user_profile_data] = self.__in_memory_user_cache.get(uuid, None)
        if found_user is None:
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=404)
        # TODO(Sean): return as json
        return str(found_user)
    
    """internal method to get specific users meal from the cache and return a response"""
    def __get_user_meal_data(self, uuid: int):
        if type(uuid) is str:
            uuid = int(uuid)
        
        print(f"[SERVER]: received GET get_user_meal_data(uuid={uuid})")
        # TODO(Sean): i don't know what the "correct" return type is for invalid get request...
        found_user: typing.Union[None, src.user.user_profile_data] = self.__in_memory_user_cache.get(uuid, None)
        if found_user is None:
            print(f"[SERVER]: could not find user_id={uuid} in cache!")
            return flask.Response(status=404)
        
        # TODO(Sean): return as json
        return str(found_user._meals)
    
"""get api call for /user/<uuid> to return user profile data"""
@flask_app.get("/user/<uuid>")
def get_user_data(uuid: int):
    return macrofi_server()._macrofi_server__get_user_data(uuid=uuid)

"""get api call for /user/meals/<uuid> to cached meals from the specified user"""
@flask_app.get("/user/meals/<uuid>")
def get_user_meal_data(uuid: int):
    return macrofi_server()._macrofi_server__get_user_meal_data(uuid=uuid)