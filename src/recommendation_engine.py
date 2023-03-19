import src.user as user
import typing
import time
import src.yelp_api

from sklearn.cluster import KMeans
import numpy as np
import src.meal_definitions
import src.usda_api
import src.server 

"""TODO document"""
class recommendation_engine:
    
    GENERIC_FOOD_PREFERENCE_LIST: typing.List[str] = ["american", "chinese", "thai", "indian", "japanese", "korean", "mexican", "italian", "fast_food"]
    # dimension of user and menu item vectors
    VECTOR_DIMENSION: int = 5
    
    def __init__(self, user: user.user_profile_data, server):
        # store the reference user we will be providing recommendations for
        self.__user: src.user.user_profile_data = user
        # store reference to owning server
        self.__server = server
    
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
    Sugar:10% of Calories
    RETURNS IN GRAMS NOW
    #https://www.prospectmedical.com/resources/wellness-center/macronutrients-fats-carbs-protein
    """
    def calculate_macronutrients(self) -> list:
        # check for programmer error
        assert self.__user is not None, "user not set!"

        calories = self.calculate_calorie_need()
        # starting factors
        carbfactor: float = 0.55
        proteinfactor: float = 0.25
        fatfactor: float = 0.30
        sugarfactor: float = 0.10

        if self.__user._personal_goal == user.user_goal_enum.WEIGHT_LOSS:
            carbfactor: float = 0.20
            proteinfactor: float = 0.45
            fatfactor: float = 0.35
            sugarfactor: float = 0.10
        
        carbs = calories*carbfactor/4 # 4 CALORIES PER GRAM
        protein = calories*proteinfactor/4 # 4 CALORIES PER GRAM
        fat = calories*fatfactor/9 # 9 CALORIES PER GRAM    
        sugar = calories*sugarfactor/4 # 4 CALORIES PER GRAM    
        # compute
        macros = [carbs, protein, fat, sugar]
        return macros
    
    """
    internal helper function to compute cosine similarity between a user vector, and matrix of menu items vectors
    """
    def __compute_cosine_similarities(self, user_vector, items_as_vector_matrix):
        
        assert user_vector.shape[0] == items_as_vector_matrix.shape[1], "shapes are not correct!"
        assert user_vector.shape[0] == recommendation_engine.VECTOR_DIMENSION, "shape does not match vector dimension!"
        
        # compute the dot product of the item matrix and user vector
        # calculates a matrix which represents how closely the user vector and each menu item vector align
        # (m x n) * (m x 1) = (n x 1) result
        P = items_as_vector_matrix.dot(user_vector)
        
        # create intermediate matrix of magnitudes of each of the menu item vectors
        # (n x 1)
        z = np.array([[np.linalg.norm(items_as_vector_matrix[i])] for i in range(items_as_vector_matrix.shape[0])])
        
        # compute a matrix of the products of the user vector and menu item magnitudes
        # helps with returning normalized results
        # scalar * (n x 1) = (n x 1) result
        Q = z * np.linalg.norm(user_vector)
        # remove possible division by zero
        Q[Q == 0] = 1.0
        
        #print(f"P: {P}\nQ: {Q}\nz: {z}\nuser: {user_vector}\n||user||: {np.linalg.norm(user_vector)}")
            
        # normalize
        return P / Q
    
    """helper function to create a nutrient dictionary containing the amount of each nutrient that a user still needs to eat for the day"""
    def __calculate_nutrient_need_dict(self, nutrient_dict: typing.Dict[str, float]) -> typing.Dict[str, float]:
        need_dict = {}
        
        calories_needed: int = self.calculate_calorie_need()
        # protein factor (percentage of total calories)
        protein_factor: float = 0.25
        # approximate calories to grams
        protein_cals_to_gram: float = 0.25
        fat_factor: float = 0.25
        fat_cals_to_gram: float = 0.25
        carbohydrate_factor: float = 0.45
        carbohydrate_cals_to_gram: float = 1 / 9
        sugar_factor: float = 0.05
        sugar_cals_to_gram: float = 0.25
        
        # protein needed is calculated as a percentage of total calories needed (in grams)
        need_dict["protein"] = (calories_needed * protein_factor * protein_cals_to_gram) - nutrient_dict.get("protein", 0)
        need_dict["carbohydrates"] = (calories_needed * carbohydrate_factor * carbohydrate_cals_to_gram) - nutrient_dict.get("carbohydrates", 0)
        need_dict["sugar"] = (calories_needed * sugar_factor * sugar_cals_to_gram) - nutrient_dict.get("sugar", 0)
        need_dict["fat"] =  (calories_needed * fat_factor * fat_cals_to_gram) - nutrient_dict.get("fat", 0)
        
        return need_dict
    
    """helper function to return a user as a vector (used when computing cosine similarity)"""
    def __vectorize_user(self):
        #print(f"[recommendation_engine]: __vectorize_user(user={self.__user}) is not finished!")
        
        user_meals: typing.List[src.meal_definitions.meal_item] = self.__server._macrofi_server__get_user_meal_data(uuid=self.__user._uuid, earliest_date=self.__server._macrofi_server__get_today_midnight())
        
        # compute the amount of calories a user needs (averaged out based on how many meals still need to be eaten)
        calories_needed = self.calculate_calorie_need()
        calories_eaten = sum([meal.get_total_calories() for meal in user_meals])
        calories_for_meal: int = calories_needed - calories_eaten 
        
        # average out based off number of meals that are still left to be eaten
        meals_needed = 3 - len(user_meals)
        meal_average_factor: float = 1 / max(meals_needed, 1)
        
        # get total nutrients consumed for the day
        all_nutrients_for_today = {}
        for meal in user_meals:
            all_nutrients_for_today.update(meal.get_total_nutrient_data())
            
        nutrient_need_dict = self.__calculate_nutrient_need_dict(nutrient_dict=all_nutrients_for_today)
        
        # create feature vector
        features = [
            [calories_for_meal * meal_average_factor],
            [nutrient_need_dict["protein"] * meal_average_factor],
            [nutrient_need_dict["carbohydrates"] * meal_average_factor],
            [nutrient_need_dict["fat"] * meal_average_factor],
            [nutrient_need_dict["sugar"] * meal_average_factor]
        ]
        
        return np.array(features)

    """internal helper function to retrieve menu items based on reference business data and menu item cache"""
    def __get_menu_items_from_business_data(self, usda_api: src.usda_api.usda_nutrient_api, business_data, menu_item_cache):
        menu_items: typing.Dict[str, src.meal_definitions.food_item] = {}
        for cuisine, businesses in business_data.items():
            for business in businesses:
                
                business_name = business["name"]
                
                # cross reference cusine and business item to retrieve menu items
                food_items: typing.List[str] = menu_item_cache[cuisine].get(business_name.lower(), [])
                if not food_items:
                    print(f"[recommendation_engine]: unable to find business '{business_name}' in menu item cache!")
                for food in food_items:
                    # api call to retrieve nutrient data if we have not looked up that item already
                    if menu_items.get(food, None) is None:
                        item_data: typing.Union[src.meal_definitions.food_item, None] = usda_api.search_call_best_as_food_item(food, can_fail=True)
                        if item_data is not None:
                            menu_items[food] = item_data
                        else:
                            print(f"[recommendation_engine]: usda_api.search_call_best_as_food_item(food={food}) returned null, something went wrong with call")
        
        return menu_items
    
    """helper function that returns a vector representation of the reference food item"""
    def __food_item_to_vector(self, food_item: src.meal_definitions.food_item):
        # NOTE: should we also include cuisine?
        features = [
            food_item._calories, 
            food_item._nutrient_data.get("protein", 0), 
            food_item._nutrient_data.get("carbohydrates", 0), 
            food_item._nutrient_data.get("fat", 0), 
            food_item._nutrient_data.get("sugar", 0)
        ]
        return np.array(features)
    
    """helper function that takes a dictionary of menu items (keyword, menu item data) and returns a dictionary of vectorized menu items"""
    def __vectorize_menu_items(self, menu_items_dict):
        
        menu_items_matrix = np.array([[None]*recommendation_engine.VECTOR_DIMENSION for _ in range(len(menu_items_dict.keys()))])
        for index, item in enumerate(menu_items_dict.values()):
            menu_items_matrix[index] = self.__food_item_to_vector(item)
        
        return menu_items_matrix

    """
    use cosine similarity to compute best results, and return top-n
    NOTE: yelp_api should probably just be passed into constructor but whatever, it's an MVP
    NOTE: user_location should also probably be cached on recommendation engine, but it's an MVP
    """
    def find_n_recommendations(self, n_recommendations, yelp_api: src.yelp_api.yelp_api, usda_api: src.usda_api.usda_nutrient_api, user_location, menu_item_cache):
        assert n_recommendations > 0, "must return at least 1 result!"
        
        # check that we have user location
        assert user_location is not None, "no user location?"
        
        # try to use user preference (cuisines), otherwise use a predefined list
        query_terms: typing.List[str] = self.__user._food_preferences if self.__user._food_preferences else recommendation_engine.GENERIC_FOOD_PREFERENCE_LIST
        # iterate terms and get restaurant data from yelp (which includes food items)
        business_data = { }
        
        debug_count: int = 0
        for term in query_terms:
            if debug_count >= 1:
                print("[recommendation_engine]: only doing 1 yelp api search call to save credits!")
                break
            
            # create one huge list of businesses
            query_data = { "term": term, "location": user_location }
            
            #print("find_n_recommendations() not actually doing yelp api call to save on credits!")
            business_data[term] = business_data.get(term, []) + yelp_api.search_for_businesses(query_data)["businesses"]
            
            debug_count += 1
        
        # get menu items from business data
        menu_items = self.__get_menu_items_from_business_data(usda_api=usda_api, business_data=business_data, menu_item_cache=menu_item_cache)
        
        print(f"[recommendation_engine]: found {len(menu_items)} different menu item results")
        
        # create vectors of business data and user
        # NOTE: items_vectorized is a np matrix of vectorized items
        items_vectorized = self.__vectorize_menu_items(menu_items_dict=menu_items)
        user_vectorized = self.__vectorize_user()
        
        # compute cosine similarity
        similarities: typing.Dict[str, float] = self.__compute_cosine_similarities(user_vector=user_vectorized, items_as_vector_matrix=items_vectorized)
        
        # create a list we can use to index into
        menu_item_keys_as_list = [key for key in menu_items.keys()]
        # sort by cosine similarity
        sorted_by_cosine_similarity = sorted(menu_items.items(), key=lambda x: similarities[menu_item_keys_as_list.index(x[0])])
        
        # get and return top-k
        return { k:v for k,v in sorted_by_cosine_similarity[:n_recommendations] }
        
        
        
    
