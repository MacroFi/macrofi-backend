import src.user as user
import typing
import time
import src.yelp_api

from sklearn.cluster import KMeans
import numpy as np

"""TODO document"""
class recommendation_engine:
    
    GENERIC_FOOD_PREFERENCE_LIST: typing.List[str] = ["american", "chinese", "thai", "indian", "japanese", "korean", "mexican", "italian", "fast_food"]
    
    def __init__(self, user: user.user_profile_data):
        # store the reference user we will be providing recommendations for
        self.__user = user
    
    # TODO(Sean): k-clustering of time eaten of meals to recommend "timely" meals?
    def kmeans_clustering_on_meals(self, number_of_meals: int = 3):
        # NOTE(Sean) this is wip
        
        # check for programmer error
        assert self.__user is not None, "user not set!"
        
        if not self.__user._meals:
            print("[recommendation_engine]: cannot perform kmeans clustering with 0 features!")
            return
        
        # converts each time eaten (datatime) to unix time
        meal_time_data = np.array([time.mktime(meal._time_eaten.timetuple()) for meal in self.__user._meals]).reshape(-1, 1)
        
        kmeans = KMeans(n_clusters=number_of_meals, n_init=10).fit(meal_time_data)
        
        # TODO recommendations based off clusters
        print(kmeans.cluster_centers_)
        
    # https://github.com/prosif/Harris-Benedict-Tool/blob/master/hbe.py  NOT USING
    """FORMULA: HARRIS-BENEDICT FORMULA"""
    def calculate_calorie_need(self) -> float:
        # check for programmer error
        assert self.__user is not None, "user not set!"
        
        # starting factors
        starting_point: float = 0.0
        weight_factor: float = 0.0
        height_factor: float = 0.0
        physical_activity_factor: float = 1.3 # TODO switch based off user activity level
        age_factor: float = 0.0
        
        # initialize factors depending on user sex
        if self.__user._sex == user.user_sex_enum.MALE:
            starting_point = 66.5
            weight_factor = 13.8
            height_factor = 5
            age_factor = 6.8
        elif self.__user._sex == user.user_sex_enum.FEMALE:
            starting_point = 65.51
            weight_factor = 9.6
            height_factor = 1.9
            age_factor = 4.7
        else:
            # TODO: what factors should we use for people who specific sex="OTHER" 
            # Might not be ethical/moral, but defaulting to Female
            starting_point = 65.51
            weight_factor = 9.6
            height_factor = 1.9
            age_factor = 4.7

        if self.__user._personal_goal == user.user_goal_enum.WEIGHT_LOSS:
            physical_activity_factor = 0.9
        if self.__user._personal_goal == user.user_goal_enum.WEIGHT_GAIN:
            physical_activity_factor = 1.1
        if self.__user._personal_goal == user.user_goal_enum.BULK:
            physical_activity_factor = 1.2
        if self.__user._personal_goal == user.user_goal_enum.LEAN:
            physical_activity_factor = 1.1
        
        # compute
        weight = (weight_factor * self.__user.get_body_weight_in_kg())
        height = (height_factor * self.__user.get_height_in_cm())
        numerator = starting_point + weight + height 
        # TODO(Sean): add physical activity factor...
        return (numerator / (age_factor * self.__user._age)) * physical_activity_factor * 100
    
    """
    Carbs: 45-65% of Calories
    Protein: 10-35% of Calories
    Fat: 20-35% of Calories
    """
    """
    def calculate_macronutrients(self) -> list:
        # check for programmer error
        assert self.__user is not None, "user not set!"

        calories = self.calculate_calorie_need()
        # starting factors
        carbfactor: float = 0.55
        proteinfactor: float = 0.20
        fatfactor: float = 0.30
        
        carbs = calories*carbfactor
        protein = calories*proteinfactor
        fat = calories*fatfactor        
        # compute
        macros = [carbs, protein, fat]
        return macros
    """
    
    """
    internal helper function to compute cosine similarity between a user vector, and matrix of menu items vectors
    """
    def __compute_cosine_similarities(self, user_vector, items_as_vector_matrix):
        
        assert user_vector.shape[1] == items_as_vector_matrix.shape[0], "shapes are not correct!"
        
        # compute the dot product of the item matrix and user vector
        # calculates a matrix which represents how closely the user vector and each menu item vector align
        # (m x n) * (m x 1) = (n x 1) result
        P = items_as_vector_matrix.dot(user_vector)
        
        # create intermediate matrix of magnitudes of each of the menu item vectors
        # (n x 1)
        z = np.array([[np.linalg.norm(items_as_vector_matrix[i]) for i in range(items_as_vector_matrix.shape[0])]])
        
        # compute a matrix of the products of the user vector and menu item magnitudes
        # helps with returning normalized results
        # scalar * (n x 1) = (n x 1) result
        Q = z @ np.linalg.norm(user_vector)
            
        # normalize
        return P / Q
    
    """helper function to return a user as a vector (used when computing cosine similarity)"""
    def __vectorize_user(self, user):
        print(f"[recommendation_engine]: __vectorize_user(user={user}) is not finished!")
        # take the amount of calories they still need, and average based on how many meals they still need to eat
        calories_for_meal: int = 0
        return np.array([])

    """internal helper function to retrieve menu items based on reference business data and menu item cache"""
    def __get_menu_items_from_business_data(self, business_data, menu_item_cache):
        print(f"[recommendation_engine]: __get_menu_items_from_business_data(business_data={business_data}) is not finished!")
        return {}
        
    """helper function that takes a dictionary of menu items (keyword, menu item data) and returns a dictionary of vectorized menu items"""
    def __vectorize_menu_items(self, menu_items_dict):
        print(f"[recommendation_engine]: __vectorize_menu_items(menu_items_dict={menu_items_dict}) is not finished!")
        return np.array([])

    """
    use cosine similarity to compute best results, and return top-n
    NOTE: yelp_api should probably just be passed into constructor but whatever, it's an MVP
    NOTE: user_location should also probably be cached on recommendation engine, but it's an MVP
    """
    def find_n_recommendations(self, n_recommendations, yelp_api: src.yelp_api.yelp_api, user_location, menu_item_cache):
        assert n_recommendations > 0, "must return at least 1 result!"
        
        # check that we have user location
        assert user_location is not None, "no user location?"
        
        # try to use user preference (cuisines), otherwise use a predefined list
        query_terms: typing.List[str] = self.__user._food_preferences if self.__user._food_preferences else recommendation_engine.GENERIC_FOOD_PREFERENCE_LIST
        # iterate terms and get restaurant data from yelp (which includes food items)
        business_data = { "businesses": [] }
        for term in query_terms:
            # create one huge list of businesses
            query_data = { "term": term, "location": user_location }
            
            print("find_n_recommendations() not actually doing yelp api call to save on credits!")
            #business_data["businesses"] = business_data["businesses"] + yelp_api.search_for_businesses(query_data)["businesses"]
        
        # get menu items from business data
        menu_items = self.__get_menu_items_from_business_data(business_data=business_data, menu_item_cache=menu_item_cache)
        
        # create vectors of business data and user
        # NOTE: items_vectorized is a np matrix of vectorized items
        items_vectorized = self.__vectorize_menu_items(menu_items_dict=menu_items)
        user_vectorized = self.__vectorize_user(user=user)
        
        # compute cosine similarity
        similarities: typing.Dict[str, float] = self.__compute_cosine_similarities(user_vector=user_vectorized, items_as_vector_matrix=items_vectorized)
        
        menu_item_keys_as_list = menu_items.keys()
        # sort by cosine similarity
        sorted_by_cosine_similarity = sorted(menu_items.items(), key=lambda x: similarities[menu_item_keys_as_list.index(x)])
        
        # get and return top-k
        return sorted_by_cosine_similarity[:n_recommendations]
        
        
        
    
