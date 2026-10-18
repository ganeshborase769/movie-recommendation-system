from database import get_all_users

users = get_all_users()

print("Total users:", len(users))

for user in users:
    print(
        "Username:", user["username"],
        "| Email:", user["email"]
    )