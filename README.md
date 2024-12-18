**Library ManagementSystem Task (Python)**

Following are steps involve to run the API.

Tech used:

Language :Python

Framework :Flask

Database : PostgreSql,SQLAlchemy (ORM)

Authentication: JWT

IDE : VSCode

API Style:REST

Please install and setup properly :

Python, Flask, Flask-sqlalchemy, flask-jwt-extended, psycopg2-Binary, Werkzeug,PostgreSQL.

Use pip install the framework, libraries.

Note : Ensure that Database(SQL) is runningin background for proper API operation.

**To test the API.**

Start thepostgresql service.

Open the Terminaland run the command – Python library.pyThe code will run, API is accessible : [http://127.0.0.1:5000](http://127.0.0.1:5000)

On line 49 of library.py, you'll find the line: db.create\_all()

This isused to create the database schema if the database does not already exist.

1.      To test authentication, login a user

        Method : POST

        http://127.0.0.1:5000/login
        
200 – Successfully authentication

400 – Invaild Input

401 - Unauthorized

2.       Create user – librarian API

        Method : POST

        http://127.0.0.1:5000/librarian/create_user

400 – Invalid Input

403 – Unauthorized access

3.       View requests

        Method : GET
        
        http://127.0.0.1:5000/librarian/view_requests

4.       Update request

        Method: PATCH

        http://127.0.0.1:5000/librarian/update_request/<int:request_id>


5.   View books – library user

        Method : GET

        http://127.0.0.1:5000/books

6.       Borrow books

        Method : POST
        
        http://127.0.0.1:5000/borrow

7.       User borrow history

        Method : GET
        
        http://127.0.0.1:5000/user/history

8.       Download borrow history

        Method : GET
        
        http://127.0.0.1:5000/user/history/download
        

**API Requirement**

Librarian APIs:

        Create a new library user with an email and password.
        View all book borrow requests.
        Approve or deny a borrow request.
        View a user’s book borrow history.

Library User APIs:

        Get list of books
        Submit a request to borrow a book for specific dates (date1 to date2).
        View personal book borrow history.

**Rules**

        A book cannot be borrowed by more than one user during the same period. (There can be multiple books of same name but each book will be considered as unique)
        Use JWT Authentication for all APIs.
        Handle all edge cases, such as:
        Invalid or incomplete requests.
        Overlapping borrow dates.
        Requests for non-existent users or books.
        Allow library users to download all their data (borrow history) as a CSV file.


