import requests
import json
import src.yelp_api

if __name__ == "__main__":
    
    meal_json = {
        "meal_name":"TEST_MEAL1",
        "food_items":["burger", "fries"]
    }
    header = {
        "Content-Type":"application/json"
    }
    
    # test PUT http://127.0.0.1:5000/v1/user/1234/meals
    try:
        requests.put("http://127.0.0.1:5000/v1/user/1234/meals", data=json.dumps(meal_json), headers=header)
    except:
        print("failed to get a respnose from http://127.0.0.1:5000/v1/user/1234/meals")
        
    # test GET http://127.0.0.1:5000/v1/user/1234/meals
    try:
        response = requests.get("http://127.0.0.1:5000/v1/user/1234/meals")
        print(response.json())
    except:
        print("failed to get response from http://127.0.0.1:5000/v1/user/1234/meals")
    
    # test GET http://127.0.0.1:5000/v1/user/1234/recommendations
    try:
        print("recommendations: ")
        response = requests.get("http://127.0.0.1:5000/v1/user/1234/recommendations")
    except:
        print("failed to get a response from http://127.0.0.1:5000/v1/user/1234/recommendations")
    
    
    #yelp_api = src.yelp_api.yelp_api()
    #yelp_api.search_for_businesses(query_data={ "term":"chinese", "location":"irvine" })
    #print(yelp_api.get_rich_business_data_by_id(business_id="wNxezrFheDjxfIfMuuqOSQ"))
    
    