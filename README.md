# macrofi-backend

## prerequisites
- requests (`pip install requests`)
- flask >= 2.0 (`pip install flask`)
- python 3.9

## running

run main.py from root directory
`python main.py`

## endpoints

`/user/{user uuid}` returns user profile data  
`/user/meals/{user uuid}` returns user's meal data

example usage:
`curl http://127.0.0.1:5000/users/{user uuid}`