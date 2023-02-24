# macrofi-backend

## prerequisites
- requests (`pip install requests`)
- flask >= 2.0 (`pip install flask`)
- sklearn (`pip install sklearn`)
- numpy (`pip install numpy`)
- python 3.9

## running

run main.py from root directory
`python main.py`

arguments
- `--headless` run in headless mode
- `--server` run the flask server
- `--port` specify port for the flask server

## endpoints

| endpoint | method | description |
| -------- | ------ | ----------- |
| `/v1/user/{uuid}` | GET, POST, PUT |  return or update user profile data |
| `/v1/user/{uuid}/meals` | GET, PUT | return all of a user's meal data or update their meals |
| `/v1/user/{uuid}/meals/today` | GET | return user's meal data from today |
| `/v1/user/{uuid}/location` | PUT | update user's current location |
| `/v1/user/{uuid}/calorie/need` | GET | return user's daily calorie need |
| `/v1/user/{uuid}/calorie/today` | GET | return user's computed calorie consumption for today |
| `/v1/user/{uuid}/nearby` | GET | return nearby, recommended restaurants for a specific user |
| `/v1/today` | GET | return the date and time used for "today" |

example usage:
`curl http://127.0.0.1:5000/v1/user/{user uuid}`
