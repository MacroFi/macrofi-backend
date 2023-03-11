import requests
import json

if __name__ == "__main__":
    
    meal_json = {
        "meal_name":"TEST_MEAL1",
        "food_items":["burger", "fries"],
        "time_eaten": "2023-10-03 10:10:10"
    }
    header = {
        "Content-Type":"application/json"
    }
    
    requests.put("http://127.0.0.1:5000/v1/user/1234/meals", data=json.dumps(meal_json), headers=header)
    
    response = requests.get("http://127.0.0.1:5000/v1/user/1234/meals")
    print(response.json())