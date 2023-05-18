print("Started Creating User")

db.createUser({
  user: 'user',
  pwd: 'password',
  roles: [
    {
      role: 'readWrite',
      db: 'order_mongodb',
    },
  ],
});

print("User created successfully")