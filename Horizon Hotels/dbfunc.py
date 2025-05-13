import mysql.connector
from mysql.connector import errorcode

hostname = "localhost"
username = "root"
passwd = "Arthur123!"

def getConnection():    
    try: #Try except to catch errors and explain them
        conn = mysql.connector.connect(host = hostname,                              
                              user = username,
                              password = passwd)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR: #If username/password is incorrect
            print('User name or Password is not working')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print('Database does not exist')
        else:
            print(err)                        
    else:  #If no errors are encountered
        return conn
                