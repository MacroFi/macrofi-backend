from src.user import user_profile_data


def main():
    # create a test user
    user1 = user_profile_data(_uuid=1234, _weight=120, _height=15, _age=20, _meals=[])
    print(user1)

if __name__ == "__main__":
    main()