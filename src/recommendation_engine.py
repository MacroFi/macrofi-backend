import src.user as user
import typing
import time

from sklearn.cluster import KMeans
import numpy as np

"""TODO document"""
class recommendation_engine:
    
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
        
        kmeans = KMeans(n_clusters=number_of_meals).fit(meal_time_data)
        
        # TODO recommendations based off clusters
        print(kmeans.cluster_centers_)
        
    """TODO: where did we get formula?"""
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
            assert False, "not implemented"
        
        # compute
        weight = (weight_factor * self.__user.get_body_weight_in_kg())
        height = (height_factor * self.__user.get_height_in_cm())
        numerator = starting_point + weight + height 
        # TODO(Sean): add physical activity factor...
        return (numerator / (age_factor * self.__user._age)) * physical_activity_factor * 100