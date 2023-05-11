# Blogging platform

## Description
### An application that allows read posts published by authorized users.</p>

## Installation

To get started, execute the following commands:

* ```pip install -r requirements.txt```
* ```cd just_blog```
* ``python manage.py migrate``
* ```python manage.py runserver```

After executing this command, the application will run in the debug mode.

The application can the debug toolbar. To turn it on in the debug mode uncomment the following lines in the settings.py:

```
INSTALLED_APPS = [
    ...
    # 'debug_toolbar',
    ...
    ]
```

```
MIDDLEWARE = [
    ...
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    ...
]
```

```
# INTERNAL_IPS = [
#     # ...
#     "127.0.0.1",
#     # ...
# ]
```

And this line in urls.py:

```
#    urlpatterns += [
#        path('__debug__/', include(debug_toolbar.urls))
#    ]
```

By default the database is populated with some example data. 
It is stored in fixtures of every app and can be deleted in the admin panel.

The admin credentials are:

username: admin

password: 123456

The password for every other user is: robot1234.


## The use of API

This application can be used as API. The specification can be found at /swagger/.

* To create a new user, use ``api/auth/users/`` endpoint. The required fields are ```username``` and ```password```.
* To get a token, user ``auth/token/login/`` endpoint. The required fields are ```username``` and ```password```.
* To logout and make your token expire, use ``auth/token/logout/`` endpoint.

## Testing

To test the application, run the ``python manage.py test`` command, or use ``multiple_tests.sh`` bash script 
to run the tests multiple times. By default, the script executes 100 iterations.


