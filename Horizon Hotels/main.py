#Name: Arthur Milner ID: 21035478
#E-Mail: arthur2.milner@live.uwe.ac.uk
#Version: 1.0
#Flask to run my website project

import mysql.connector, dbfunc
from flask import Flask, render_template, request, flash, redirect, url_for, session, abort
from mysql.connector import Error, errorcode
from markupsafe import escape
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "hello"
DB_NAME = "horizon_hotels"


@app.route("/aboutus") #Route for the about us page
@app.route("/")        
def aboutus():
   print("About Us")
   checkFirstVisit()
   return render_template("aboutus.html")



@app.route("/makebooking", methods=["POST", "GET"]) #route for the make booking page
def makebooking():
   checkLoggedIn()
   checkFirstVisit()
   if request.method == "POST": #This code gets the location dependant on which button the user presses and sends it over to the confirm booking page
        bookingLocation = request.form["book-button"] #Gets the value of the pressed button
        return redirect(url_for("confirmbooking", location= escape(bookingLocation))) #Redirects to the confirm booking page whilst sending over the variable for location
   return render_template("makebooking.html")



@app.route("/managebooking", methods=["POST", "GET"]) #route for the manage booking page
def managebooking():
   checkLoggedIn()
   checkFirstVisit()
   if request.method == "POST": #Runs once a user presses the submit button to cancel a booking
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            bookingID = request.form["booking-code"]
            userAndBookingDataset = (session.get("CurrentUserID"), bookingID)
            bookingIDDataset = (bookingID, )
            checkUserOwnsBookingStatement = "SELECT booking_id\
                                                FROM bookings\
                                                WHERE user_id = %s AND booking_id = %s;"
            getBookingPriceStatement = "SELECT booking_price FROM bookings \
                                                             WHERE booking_id = %s;" #Gets price of the booking being cancelled
            getCurrencyStatement = "SELECT currency_symbol \
                                                      FROM currencies NATURAL JOIN bookings\
                                                      WHERE booking_id = %s;"
            getDaysUntilCheckInStatement = "SELECT DATEDIFF(booking_check_in, NOW())\
                                                                  FROM bookings \
                                                                  WHERE booking_id = %s;"
            findRoomType = "SELECT room_size FROM bookings \
                                          WHERE booking_id = %s;"
            updateStandard = "UPDATE hotels h NATURAL JOIN bookings b\
                                             SET h.standard_capacity = h.standard_capacity + 1\
                                             WHERE \
                                                b.room_size = 'Standard' AND\
                                                b.booking_id = %s;"
            updateDouble = "UPDATE hotels h NATURAL JOIN bookings b\
                                          SET h.double_capacity = h.double_capacity + 1\
                                          WHERE \
                                             b.room_size = 'Double' AND\
                                             b.booking_id = %s;"
            updateFamily = "UPDATE hotels h NATURAL JOIN bookings b\
                                    SET h.family_capacity = h.family_capacity + 1\
                                    WHERE \
                                       b.room_size = 'Family' AND\
                                       b.booking_id = %s;"
            deleteBookingStatement = "DELETE FROM bookings b\
                                          WHERE b.booking_id = %s;"
            print("MySQL Connection is established.")
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(checkUserOwnsBookingStatement, userAndBookingDataset)
            row = dbcursor.fetchone()
            if row != None: #Runs if the user owns the booking and the booking exists
               print("User owns the booking, calculating booking price.")
               dbcursor.execute(getBookingPriceStatement, bookingIDDataset)
               row = dbcursor.fetchone()
               cancellationFee = float(''.join(map(str, row))) #Stores the price of the booking in a variable as an int, ready to calculate cancellation cost
               print("Getting currency of the booking.")
               dbcursor.execute(getCurrencyStatement, bookingIDDataset)
               row = dbcursor.fetchone()
               currency = "".join(row)
               dbcursor.execute(getDaysUntilCheckInStatement, bookingIDDataset)
               row = dbcursor.fetchone()
               daysUntilCheckIn = int(''.join(map(str, row))) #Gets the days before the bookings check-in date and stores it as int in a variable
               print("The booking had", daysUntilCheckIn, "days until check-in.") #Print statement for debugging
               if(daysUntilCheckIn > 60): #If statement to calculate the cancellation fee, using the number of days until the bookings check-out date
                  print("There is no cancellation fee, changing hotel capacity and deleting the booking.")
                  cancellationFee = 0
               elif (30 <= daysUntilCheckIn <= 60):
                  cancellationFee = round(cancellationFee * 0.5, 2)
                  print("The cancellation fee will be {}".format(currency + str(cancellationFee)))
               elif (daysUntilCheckIn < 30):
                  cancellationFee = round(cancellationFee, 2)
                  print("The cancellation fee will be {}".format(currency + str(cancellationFee)))
               dbcursor.execute(findRoomType, bookingIDDataset)
               row = dbcursor.fetchone()
               roomSize = "".join(row)
               if(roomSize == "Standard"): #Changes the hotel capcacity dependant on room size
                  print("Changing standard capacity.")
                  dbcursor.execute(updateStandard, bookingIDDataset)
               elif(roomSize == "Double"):
                  print("Changing double capacity.")
                  dbcursor.execute(updateDouble, bookingIDDataset)
               elif(roomSize == "Family"):
                  print("Changing family capacity.")
                  dbcursor.execute(updateFamily, bookingIDDataset)
               print("Deleting booking.")
               dbcursor.execute(deleteBookingStatement, bookingIDDataset) #Deletes the booking from the database
               conn.commit()
               dbcursor.close()
               conn.close()
               if cancellationFee > 0: #Flashes if the booking has a cancellation fee
                  flash("Your booking has been cancelled, you have been charged {}.".format(currency + str(cancellationFee)))
               else: #Flashes if the booking does not have a cancellation fee
                  flash("Your booking has been cancelled and you have not been charged.")
               return redirect(url_for("managebooking"))
            else: #If the user either attempts to cancel a booking they do not own or a non-existent booking this will run
               print("User does not own this booking or it does not exist, unable to cancel.")
               flash("Error: Either the booking does not exist, or you do not own the booking you have attempted to cancel.")
               dbcursor.close()
               conn.close()
               return redirect(url_for("managebooking"))
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to cancel your booking.")
            return redirect(url_for("managebooking"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to cancel your booking.")
         return redirect(url_for("managebooking"))
   elif request.method == "GET": #When user accesses the page their bookings will be displayed to them
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            showBookingsStatement = "SELECT b.booking_id, h.location_name, b.booking_check_in,\
                                                         b.booking_check_out, b.booking_price\
                                                         FROM bookings b \
                                                         INNER JOIN hotels h ON b.hotel_id = h.hotel_id\
                                                         INNER JOIN users u ON b.user_id = u.user_id\
                                                         WHERE b.user_id = '%s'\
                                                         ORDER BY b.booking_id ASC;"
            headings = ("Booking Code:", "Location:", "Check-In:", "Check-Out:", "Price:")
            print("MYSQL connection established.")
            dataset = (session.get("CurrentUserID"), )
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(showBookingsStatement, dataset)
            print("Select statement successfully executed.")
            bookings = dbcursor.fetchall()
            print("Total Bookings: ", dbcursor.rowcount)
            dbcursor.close()
            conn.close()
            return render_template("managebooking.html", headings = headings, bookings = bookings) #Passing the headings and bookings for the dynamic table to be generated
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to access your bookings.")
            return redirect(url_for("aboutus"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to access your bookings.")
         return redirect(url_for("aboutus"))


#Route for the confirm booking page, the location variable is recieved from the makebooking page and fills in the location part of the form automatically
@app.route("/confirmbooking/<location>", methods=["POST", "GET"])
def confirmbooking(location):
   checkLoggedIn()
   checkFirstVisit()
   if request.method == "POST":
      #Gets booking information details from the user submitted form
      location = int(request.form["location"])
      roomSize = int(request.form["room-size"])
      numOfGuests = int(request.form["num-of-guests"])
      checkInDate = request.form["check-in"]
      checkOutDate = request.form["check-out"]
      currency = int(request.form["currency"])
     
      errorCounter = 0 #To track if there are any faults with the booking i.e. too many guests for room size

      checkInDateAsDate = datetime.strptime(checkInDate, '%Y-%m-%d') #Storing check-in date as a date
      checkOutDateAsDate = datetime.strptime(checkOutDate, '%Y-%m-%d') #Storing check-out date as a date
      currentDate = datetime.now()
      currentDate = currentDate.strftime("%Y-%m-%d")
      currentDate = datetime.strptime(currentDate, "%Y-%m-%d") #Storing current date as a date variable

      #IF statements to validate whether the booking is valid in accordance to the assignment requirements 
      if (roomSize == 1) and (numOfGuests > 1): #Checks if there are too many guests for the room type
         print("Too many guests")
         flash("Error: A standard room can only accomodate a single guest.")
         errorCounter = errorCounter + 1
      if (roomSize == 2) and (numOfGuests > 2): #Checks if there are too many guests for the room type
         print("Too many guests")
         flash("Error: A double room can only accomodate a maximum of two guests.")
         errorCounter = errorCounter + 1
      if checkInDateAsDate > checkOutDateAsDate: #Checks whether the check-in date is bigger than the check-out date
         print("Check-in date after check-out date")
         flash("Error: Check-in date cannot be after check-out date.")
         errorCounter = errorCounter + 1
      if checkInDateAsDate < currentDate: #Checks whetehr the check-in date is before the current date
         print("Check-in date before the current date")
         flash("Error: Check-in date cannot be before the current date.")
         errorCounter = errorCounter + 1
      if checkOutDateAsDate < currentDate: #Checks whether the check-out date is before the current date
         print("Check-out date before the current date")
         flash("Error: Check-out date cannot be before the current date.")
         errorCounter = errorCounter + 1
      if checkOutDateAsDate == currentDate: #Checks whether the check-out date is equal to the current date
         print("Check-out date on current date")
         flash("Error: Check-out date cannot be on the current date.")
         errorCounter = errorCounter + 1
      if (checkInDateAsDate - currentDate).days > 93: #Checks the booking has not been made further than 3 months in advanced
         print("Booking made too far in advanced")
         flash("Error: Bookings cannot be made greater than three months in advanced.")
         errorCounter = errorCounter + 1
      
      if errorCounter > 0: #When the booking has one or more issues this bit of code will run
         return render_template("confirmbooking.html", location = location)
      else:  #When the booking is valid and ready to be sent to the database this code will run
         conn = dbfunc.getConnection()
         if conn != None:
            try:
               print("MYSQL connection established.")
               checkInDateMonth = int(datetime.strptime(checkInDate, '%Y-%m-%d').month) #Stores the month of the check in date
               checkOutDateMonth = int(datetime.strptime(checkOutDate, '%Y-%m-%d').month) #Stores the month of the check out date
               hotelIDDataset = (location, )
               getPeakPriceStatement = "SELECT peak_cost\
                                       FROM hotels\
                                       WHERE hotel_id = %s;"
               getOffPeakPriceStatement = "SELECT off_peak_cost\
                                       FROM hotels\
                                       WHERE hotel_id = %s;"
               insertBookingStatement = "INSERT INTO bookings \
                                          (user_id,\
                                          hotel_id, \
                                          currency_id, \
                                          booking_check_in, \
                                          booking_check_out, \
                                          room_size, \
                                          number_of_guests, \
                                          booking_price)\
                                          VALUES\
                                          (%s, %s, %s, %s, %s, %s, %s, %s);"
               checkStandardCapacityStatement = "SELECT standard_capacity\
                                             FROM hotels\
                                             WHERE hotel_id = %s AND standard_capacity = 0;"
               checkDoubleCapacityStatement = "SELECT double_capacity\
                                             FROM hotels\
                                             WHERE hotel_id = %s AND double_capacity = 0;"
               checkFamilyCapacityStatement = "SELECT family_capacity\
                                             FROM hotels\
                                             WHERE hotel_id = %s AND family_capacity = 0;"
               dbcursor = conn.cursor()
               dbcursor.execute("USE {};".format(DB_NAME))
               if roomSize == 1: #Checking whether the hotel has enough capacity left for the booking to be made
                  print("Checking standard capacity")
                  dbcursor.execute(checkStandardCapacityStatement, hotelIDDataset)
                  row = dbcursor.fetchone()
                  if row != None:
                     flash("We're sorry but that hotel appears to have ran out of available standard rooms.")
                     dbcursor.close()
                     conn.close()
                     return render_template("confirmbooking.html", location = location)
               elif roomSize == 2: #Checking whether the hotel has enough capacity left for the booking to be made
                  print("Checking standard capacity")
                  dbcursor.execute(checkDoubleCapacityStatement, hotelIDDataset)
                  row = dbcursor.fetchone()
                  if row != None:
                     flash("We're sorry but that hotel appears to have ran out of available double rooms.")
                     dbcursor.close()
                     conn.close()
                     return render_template("confirmbooking.html", location = location)
               elif roomSize == 3: #Checking whether the hotel has enough capacity left for the booking to be made
                  print("Checking family capacity")
                  dbcursor.execute(checkFamilyCapacityStatement, hotelIDDataset)
                  row = dbcursor.fetchone()
                  if row != None:
                     flash("We're sorry but that hotel appears to have ran out of available family rooms.")
                     dbcursor.close()
                     conn.close()
                     return render_template("confirmbooking.html", location = location)

               #Checks whether the booking is in peak times and using peak/off-peak price based on this information
               if (4 <= checkInDateMonth <= 9) or (4 <= checkOutDateMonth <= 9):
                  print("Using peak price for the booking.")
                  dbcursor.execute(getPeakPriceStatement, hotelIDDataset)
                  row = dbcursor.fetchone()
                  bookingPrice = float(''.join(map(str, row)))
               else: #Uses off-peak price
                  print("Using off-peak price for the booking.")
                  dbcursor.execute(getOffPeakPriceStatement, hotelIDDataset)
                  row = dbcursor.fetchone()
                  bookingPrice = float(''.join(map(str, row)))

               #Changing the booking price depending on the number of guests and the room size
               if (roomSize == 2) and (numOfGuests == 2): 
                  print("Using double room with two guests premium.")
                  roomSize = "Double"
                  roomPricePremium = 1.3
               elif (roomSize == 2):
                  print("Using double room premium.")
                  roomSize = "Double"
                  roomPricePremium = 1.2
               elif (roomSize == 3):
                  print("Using family room premium.")
                  roomSize = "Family"
                  roomPricePremium = 1.5
               else:
                  print("Using standard room premium.")
                  roomSize = "Standard"
                  roomPricePremium = 1.0
               bookingPrice = bookingPrice * roomPricePremium

               #Changing booking price depending on the type of currency used to pay
               if (currency == 2): 
                  print("Using USD conversion rate.")
                  currencyConversion = 1.6
                  currencySymbol = "$"
               elif (currency == 3):
                  print("Using Euros conversion rate.")
                  currencyConversion = 1.2
                  currencySymbol = "€"
               else:
                  print("Using GBP conversion rate.")
                  currencyConversion = 1
                  currencySymbol = "£"
               bookingPrice = bookingPrice * currencyConversion


               daysInAdvanced = (checkInDateAsDate - currentDate).days #Value for how many days in advanced the booking was made
               if 45 <= daysInAdvanced <= 59: #If/elif statement to change the booking price depending on the number of days
                  print("Discount for 45-90 days in advance booking.")
                  daysInAdvanceDiscount = 0.95
               elif 60 <= daysInAdvanced <= 79:
                  print("Discount for 60-79 days in advance booking.")
                  daysInAdvanceDiscount = 0.90
               elif 80 <= daysInAdvanced <= 90:
                  print("Discount for 80-90 days booking.")
                  daysInAdvanceDiscount = 0.80
               else:
                  print("No discount for days in advance.")
                  daysInAdvanceDiscount = 1
               bookingPrice = bookingPrice * daysInAdvanceDiscount

               #Number of nights is calculated here and the booking price is then multiplied by this value
               daysOfStay = datetime.strptime(checkOutDate, '%Y-%m-%d') - datetime.strptime(checkInDate, '%Y-%m-%d')
               print("Booking is for this many nights:",int(daysOfStay.days))
               bookingPrice = bookingPrice * int(daysOfStay.days)
               
               #Inserts final booking price along with other booking details into the database
               print("The booking price is:", bookingPrice)
               bookingDataset = (session.get("CurrentUserID"), location, currency, checkInDate, checkOutDate, roomSize, numOfGuests, bookingPrice)
               dbcursor.execute(insertBookingStatement, bookingDataset) #Inserts the booking with all the details
               dbcursor.execute('SELECT LAST_INSERT_ID();') #Gets booking ID as it was last ID entered
               row = dbcursor.fetchone()
               bookingCode = int(''.join(map(str, row))) #Stores booking ID in variable to be used with the receipt and update statements below
               if roomSize == "Standard": #Changes hotel capacities to reflect the capacity after a new booking has been added
                  print("Changing standard capacity.")
                  standardCapacityUpdateStatement = "UPDATE hotels\
                                                   SET standard_capacity = standard_capacity - 1\
                                                   WHERE hotel_id = %s;"
                  dbcursor.execute(standardCapacityUpdateStatement, hotelIDDataset)
               elif roomSize == "Double":
                  print("Changing double capacity.")
                  doubleCapacityUpdateStatement = "UPDATE hotels\
                                                   SET double_capacity = double_capacity - 1\
                                                   WHERE hotel_id = %s;"
                  dbcursor.execute(doubleCapacityUpdateStatement, hotelIDDataset)
               elif roomSize == "Family":
                  print("Changing family capacity.")
                  familyCapacityUpdateStatement = "UPDATE hotels\
                                                   SET family_capacity = family_capacity - 1\
                                                   WHERE hotel_id = %s;"
                  dbcursor.execute(familyCapacityUpdateStatement, hotelIDDataset)
               conn.commit()
               dbcursor.close()
               conn.close()
               #Redirects to booking complete page with the booking details
               return redirect(url_for("bookingcomplete", code = escape(bookingCode), currency = escape(currencySymbol), price = escape(bookingPrice))) 
            except mysql.connector.Error as e:
               print(e)
               flash("Error: An error occured when attempting to create your booking.")
               return render_template("makebooking.html")
         else:
            print("Database connection error.")
            flash("Error: Connection error occured when attempting to create your booking.")
            return render_template("makebooking.html")
   return render_template("confirmbooking.html", location = location)



@app.route("/contactus", methods=["POST", "GET"]) #route for the contact us page
def contactus():
   checkFirstVisit()
   if request.method == "POST":
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            print("MYSQL connection established.")
            name = request.form["queryname"] #Stores the value submitted into the name field
            email = request.form["queryemail"] #Stores the value submitted into the email field
            subject = request.form["querysubject"] #Stores the value submitted into the subject field
            details = request.form["querydetails"] #Stores the value submitted into the query details field
            query = (name, email, subject, details)
            insertQueryStatement = "INSERT INTO queries \
                                       (query_name, \
                                       query_email, \
                                       query_subject, \
                                       query_details) \
                                    VALUES \
                                       (%s, %s, %s, %s);" #Inserts the queries details into the db
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(insertQueryStatement, query)
            print(query)
            print("Insert statement successfully executed.")
            flash("Thank you {}, query has successfully sent and is being handled, thank you for your patience.".format(name)) #Message to show when query is successfully sent to db
            conn.commit()
            dbcursor.close()
            conn.close()
            return render_template("contactus.html")
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to send your query.")
            return render_template("contactus.html")
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to access your bookings.")
         return render_template("contactus.html")
   return render_template("contactus.html")



@app.route("/signuplogin", methods=["POST", "GET"]) #route for the sign-up/log-in page
def signuplogin():
   checkFirstVisit()
   print("signuplogin")
   if request.method == "POST":
      formName = request.form['form-loginsignup'] #To differentiate between the login and sign up form
      if formName == "login-form":
         conn = dbfunc.getConnection()
         if conn != None:
            try:
               email = request.form["user-email"]
               password = request.form["user-password"] #Will get checked against the hashed value
               emailDataset = (email, )
               getHashedPasswordStatement = "SELECT password_hash\
                                             FROM users\
                                             WHERE email = %s;"
               checkAccountExistsStatement = "SELECT * FROM users\
                                    WHERE email = %s AND password_hash = %s;"
               checkIfAdminStatement = "SELECT * FROM users\
                                    WHERE email = %s AND password_hash = %s\
                                    AND is_admin = 'Admin';"
               getUserIDStatement = "SELECT user_id FROM users\
                                    WHERE email = %s and password_hash = %s;"
               dbcursor = conn.cursor()
               dbcursor.execute("USE {};".format(DB_NAME))
               dbcursor.execute(getHashedPasswordStatement, emailDataset)
               row = dbcursor.fetchone()
               if row != None: #Fetches if account exists
                  password_hash = "".join(row)
               else:
                  print("Account not found.") 
                  flash("Error: That username/password has not been recognised.")
                  return redirect(url_for("signuplogin"))
               if check_password_hash(password_hash, password) == True: #Checks password hash matches given password
                  dataset = (email, password_hash)
                  dbcursor.execute(checkAccountExistsStatement, dataset)
                  row = dbcursor.fetchone()
                  if row != None: #Runs if email and password is correct
                     print("Account found, checking if admin or user.")
                     dbcursor.execute(checkIfAdminStatement, dataset) #Checks if the account is an admin or a user
                     row = dbcursor.fetchone()
                     if row != None:
                        print("User is admin.")
                        session["AdminStatus"] = "Admin" #Sets session value admin status to admin, allowing access to the admin page
                     else:
                        print("User is not admin.")
                        session["AdminStatus"] = "User" #Sets session value admins status to user, rejecting access to admin page
                     dbcursor.execute(getUserIDStatement, dataset)
                     row = dbcursor.fetchone()
                     userID = int(''.join(map(str, row)))
                     session["CurrentUserID"] = userID #Stores the user ID of the currently logged in user
                     print("Currently logged in with user ID: ", session["CurrentUserID"])
                     if session["AdminStatus"] == "User": #Checks whether the logged in user is an admin
                        flash("You have successfully logged in with the email: {}.".format(email))
                        dbcursor.close()
                        conn.close()
                        return redirect(url_for("aboutus"))
                     elif session["AdminStatus"] == "Admin": #If user is admin they will immediately be redirected to the admin page
                        return redirect(url_for("adminpage"))
                  else: #Runs if the email/password has not been recognised
                     print("Account not found.") 
                     flash("Error: That username/password has not been recognised.")
                     return redirect(url_for("signuplogin"))
               else: #Runs if passsword entered is not correct
                  print("Password entered does not match password hash.")
                  flash("Error: That username/password has not been recognised.") 
                  return redirect(url_for("signuplogin"))
            except mysql.connector.Error as e:
                  print(e)
                  flash("Error: An error occured when attempting to log-in.")
                  return redirect(url_for("signuplogin"))
         else:
            print("Database connection error.")
            flash("Error: Connection error occured when attempting to log-in.")
            return redirect(url_for("signuplogin"))
      elif formName == "signup-form":
         conn = dbfunc.getConnection()
         if conn != None:
            try:
               email = request.form["new-email"] #Stores the value submitted into the email field
               password_hash = generate_password_hash(request.form["new-password"], method="sha256") #Stores the value submitted into the password field as hashed password
               dataset = (email, password_hash)
               emailDataset= (email, )
               insertNewUserStatement = "INSERT INTO users \
                                          (email, password_hash) VALUES (%s, %s);" #Inserts the new account details into the database
               emailInUseStatement = "SELECT * FROM  users \
                                       WHERE email = %s;" #Checks if the email is in use
               setIfAdminStatement = "UPDATE users SET is_admin = 'Admin'\
                                       WHERE email LIKE '%@admin.com';" #Sets the admin status of the account
               dbcursor = conn.cursor()
               dbcursor.execute("USE {};".format(DB_NAME))
               dbcursor.execute(emailInUseStatement, emailDataset)
               row = dbcursor.fetchone()
               if row != None: #Runs if the email is already in use
                  print("Email already in use.")
                  flash("Error: That email is already registered, failed to register a new account.")
                  dbcursor.close()
                  conn.close()
                  return redirect(url_for("signuplogin"))
               else: #Runs if the email is not already in use
                  print("Email is not in use, adding user now...")
                  dbcursor.execute(insertNewUserStatement, dataset)
                  print('User added successfully.')
                  dbcursor.execute(setIfAdminStatement)
                  print("Checked if new user is admin and updated their is_admin status.")
                  conn.commit()
                  dbcursor.close()
                  conn.close()
                  flash("User with the email {} has been added, you can now log-in.".format(email))
                  return redirect(url_for("signuplogin"))
            except mysql.connector.Error as e:
               print(e)
               flash("Error: An error occured when attempting to sign-up.")
               return redirect(url_for("signuplogin"))
         else:
            print("Database connection error.")
            flash("Error: Connection error occured when attempting to create a new account.")
            return redirect(url_for("signuplogin"))
   elif request.method == "GET": #Will run when user presses log-out button, this clears the current session variables concerned with being logged-in
      if session.get("CurrentUserID") != None:
         print("Clearing session variables.")
         flash("User successfully logged out.")
         session.pop("CurrentUserID",None)
         session.pop("AdminStatus",None)
      return render_template("signuplogin.html")



@app.route("/changepassword", methods=["POST", "GET"]) #route for the change password page
def changepassword():
   checkFirstVisit()
   print ("Change Password")
   if request.method == "POST": #Will trigger when the form from changepassword.html is submitted
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            email = request.form["forgotpass-email"] #Stores the value submitted into the email field
            password_hash = generate_password_hash(request.form["forgotpass-password"], method="sha256") #Stores the value submitted into the password field hashed
            dataset = (password_hash, email)
            emailDataset = (email, )
            emailInUseStatement = "SELECT email FROM users \
                                                   WHERE email = %s;" #Will check whether the email is tied to an account
            passwordChangeStatement = "UPDATE users SET password_hash = %s \
                                                               WHERE email = %s;" #Will execute if email is tied to an account
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(emailInUseStatement, emailDataset)
            row = dbcursor.fetchone()
            if row != None: #Runs if the email is in use
               print("Password changing...")
               dbcursor.execute(passwordChangeStatement, dataset)
               conn.commit()
               dbcursor.close()
               conn.close()
               flash("Password for {} has been succesfully changed.".format(email))
               return redirect(url_for("signuplogin"))
            else: #Will run if email is not tied to an account
               print("Email not in use")
               flash("Error: That email is not registered to an account.")
               dbcursor.close()
               conn.close()
               return redirect(url_for("changepassword"))
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to change your password.")
            return redirect(url_for("changepassword"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to change your password.")
         return redirect(url_for("aboutus"))
   return render_template("changepassword.html")

@app.route("/bookingcomplete/<code>/<currency><price>", methods=["POST", "GET"]) #Page which is displayed to the user once their booking is completed, it will display the key features of the booking
def bookingcomplete(code, currency, price):
   checkLoggedIn() 
   checkFirstVisit()
   if request.method == "POST":
      return redirect(url_for("downloadreceipt", code = escape(code), currency = escape(currency), price = escape(price)))
   return render_template("bookingcomplete.html", code= code, currency = currency, price = price)

@app.route("/downloadreceipt/<code>/<currency>/<price>") #Route which will download a reciept containing key features of the booking
def downloadreceipt(code, currency, price):
   checkLoggedIn()
   checkFirstVisit()
   return render_template("receipttemplate.html", code = code, currency = currency, price = price)

@app.route("/admin")
def adminpage():
   checkFirstVisit()
   checkAdmin()
   return render_template("adminpage.html")

#Route for admin page to manage users, cannot delete users before they delete their bookings
@app.route("/manageusers", methods=["POST", "GET"])
def manageusers():
   checkFirstVisit()
   checkAdmin()
   if request.method == "POST":
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            userEmail = request.form["user-email"]
            userEmailDataset = (userEmail, )
            selectUserStatement = "SELECT * FROM users\
                                 WHERE email = %s;"
            checkUsersBookings = "SELECT COUNT(booking_id)\
                                 FROM bookings b\
                                 NATURAL JOIN users u\
                                 WHERE u.email = %s;"
            deleteUserStatement = "DELETE FROM users\
                                    WHERE email = %s;"
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(selectUserStatement, userEmailDataset)
            row = dbcursor.fetchone()
            if row != None:
               print("User found, checking for any active bookings...")
               dbcursor.execute(checkUsersBookings, userEmailDataset)
               row = dbcursor.fetchone()
               row = int(''.join(map(str, row)))
               print("User has "+ str(row) +" current bookings.")
               if row > 0: #Runs when user has active booking
                  print("User has active bookings, cannot be deleted.")
                  flash("Error: User has active bookings and cannot be deleted.")
                  return redirect(url_for("manageusers"))
               else: #Runs when user exists and has no active bookings
                  print("User has no bookings, deleting the user now...")
                  dbcursor.execute(deleteUserStatement, userEmailDataset)
                  conn.commit()
                  dbcursor.close()
                  conn.close()
                  flash("User succesfully deleted.")
                  return redirect(url_for("manageusers"))
            print("User not found.")
            flash("Error: User was not found.")
            return redirect(url_for("manageusers"))
         except mysql.connector.Error as e:
               print(e)
               flash("Error: An error occured when attempting to delete the user.")
               return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to delete the user.")
         return redirect(url_for("adminpage"))
   elif request.method == "GET": #When admin accesses the page all users will be displayed to them
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            showUserEmailsStatement = "SELECT email\
                                       FROM users\
                                       WHERE is_admin = 'User'\
                                       ORDER BY email ASC;"
            print("MYSQL connection established.")
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(showUserEmailsStatement)
            print("Select statement successfully executed.")
            users = dbcursor.fetchall()
            print("Total Users Found: ", dbcursor.rowcount)
            dbcursor.close()
            conn.close()
            return render_template("manageusers.html", users=users)
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to access users.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting access users.")
         return redirect(url_for("adminpage"))

#Route for admin page to manage user bookings
@app.route("/manageuserbookings", methods=["POST", "GET"])
def manageuserbookings():
   checkFirstVisit()
   checkAdmin()
   if request.method == "POST":
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            bookingID = request.form["booking-code"]
            bookingIDDataset = (bookingID, )
            adminSelectBookingStatement = "SELECT * FROM bookings\
                                          WHERE booking_id = %s;"
            adminDeleteBookingStatement = "DELETE FROM bookings\
                                          WHERE booking_id = %s;"
            updateStandard = "UPDATE hotels h NATURAL JOIN bookings b\
                                 SET h.standard_capacity = h.standard_capacity + 1\
                                 WHERE \
                                    b.room_size = 'Standard' AND\
                                    b.booking_id = %s;"
            updateDouble = "UPDATE hotels h NATURAL JOIN bookings b\
                              SET h.double_capacity = h.double_capacity + 1\
                              WHERE \
                                 b.room_size = 'Double' AND\
                                 b.booking_id = %s;"
            updateFamily = "UPDATE hotels h NATURAL JOIN bookings b\
                              SET h.family_capacity = h.family_capacity + 1\
                              WHERE \
                                 b.room_size = 'Family' AND\
                                 b.booking_id = %s;"
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(adminSelectBookingStatement, bookingIDDataset)
            row = dbcursor.fetchone()
            if row != None:
               print("Booking found, updating capacity and deleting now...")
               print("Updating hotel capcaity...")
               dbcursor.execute(updateStandard, bookingIDDataset)
               dbcursor.execute(updateDouble, bookingIDDataset)
               dbcursor.execute(updateFamily, bookingIDDataset)
               print("Deleting booking...")
               dbcursor.execute(adminDeleteBookingStatement, bookingIDDataset)
               print("Booking deleted.")
               conn.commit()
               dbcursor.close()
               conn.close()
               flash("Booking has been successfully deleted.")
               return redirect(url_for("manageuserbookings"))
            print("Booking not found.")
            flash("Error: The booking could not be found.")
            return redirect(url_for("manageuserbookings"))
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to delete the booking.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to delete the booking.")
         return redirect(url_for("adminpage"))
   elif request.method == "GET": #When user accesses the page their bookings will be displayed to them
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            showEmailAndBookingIDStatement = "SELECT u.email, b.booking_id\
                                             FROM users u\
                                             INNER JOIN bookings b ON u.user_id = b.user_id\
                                             ORDER BY u.email ASC;"
            headings = ("User Email:", "Booking Code:")
            print("MYSQL connection established.")
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(showEmailAndBookingIDStatement)
            print("Select statement successfully executed.")
            bookings = dbcursor.fetchall()
            print("Total Bookings Found: ", dbcursor.rowcount)
            dbcursor.close()
            conn.close()
            return render_template("manageuserbookings.html", headings=headings, bookings=bookings)
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to access user bookings.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to access your bookings.")
         return redirect(url_for("adminpage"))

@app.route("/edithotels", methods=["POST", "GET"])
def edithotels():
   checkFirstVisit()
   checkAdmin()
   if request.method == "POST": #Updates specific query to archived
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            hotelID = request.form["edit-id"]
            offPeakPrice = request.form["edit-offpeak"]
            peakPrice = request.form["edit-peak"]
            standardCapacity = request.form["edit-standard"]
            doubleCapacity = request.form["edit-double"]
            familyCapacity = request.form["edit-family"]
            hotelIDDataset = (hotelID, )
            updateHotelDataset = (offPeakPrice, peakPrice, standardCapacity, doubleCapacity, familyCapacity, hotelID)
            updateQueryStatement = "UPDATE hotels\
                                    SET off_peak_cost = %s,\
                                    peak_cost = %s,\
                                    standard_capacity = %s,\
                                    double_capacity = %s,\
                                    family_capacity = %s\
                                    WHERE hotel_id = %s;"
            selectQueryStatement = "SELECT * FROM hotels\
                                    WHERE hotel_id = %s;"
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(selectQueryStatement, hotelIDDataset)
            row = dbcursor.fetchone()
            if row != None: #Runs if hotel exists
               print("Hotel exists, updating now...")
               dbcursor.execute(updateQueryStatement, updateHotelDataset)
               print("Hotel updated.")
               conn.commit()
               dbcursor.close()
               conn.close()
               flash("Hotel has been successfully updated.")
               return redirect(url_for("edithotels"))
            print("Hotel does not exist")
            flash("Error: Hotel was not found.")
            return redirect(url_for("edithotels"))
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to update the hotel.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to update the hotel.")
         return redirect(url_for("adminpage"))
   elif request.method == "GET":
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            getHotelInfoStatement = "SELECT * FROM hotels;"
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(getHotelInfoStatement)
            hotels = dbcursor.fetchall()
            print("Total Hotels Found: ", dbcursor.rowcount)
            dbcursor.close()
            conn.close()
            return render_template("edithotels.html", hotels=hotels)
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to update the query.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to update the query.")
         return redirect(url_for("adminpage"))

#Route to view queries as an admin
@app.route("/viewqueries", methods=["POST", "GET"])
def viewqueries():
   checkFirstVisit()
   checkAdmin()
   if request.method == "POST": #Updates specific query to archived
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            queryID = request.form["query-code"]
            queryIDDataset = (queryID, )
            updateQueryStatement = "UPDATE queries\
                                    SET query_status = 'Archived'\
                                    WHERE query_id = %s;"
            selectQueryStatement = "SELECT * FROM queries\
                                    WHERE query_id = %s AND query_status = 'Active';"
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(selectQueryStatement, queryIDDataset)
            row = dbcursor.fetchone()
            if row != None: #Runs if query exists
               print("Query exists, updating now...")
               dbcursor.execute(updateQueryStatement, queryIDDataset)
               print("Query updated.")
               conn.commit()
               dbcursor.close()
               conn.close()
               flash("Query has been successfully archived.")
               return redirect(url_for("viewqueries"))
            print("Query does not exist")
            flash("Error: Query was not found.")
            return redirect(url_for("viewqueries"))
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to update the query.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to update the query.")
         return redirect(url_for("adminpage"))
   elif request.method == "GET": #Lists all queries within the db
      conn = dbfunc.getConnection()
      if conn != None:
         try:
            showQueryDetailsStatement = "SELECT query_id, query_name, query_email, query_subject, query_details\
                                             FROM queries\
                                             WHERE query_status = 'Active'\
                                             ORDER BY query_email ASC;"
            headings = ("Query ID:", "Query Name:", "Query Email:", "Query Subject:", "Query Details:")
            print("MYSQL connection established.")
            dbcursor = conn.cursor()
            dbcursor.execute("USE {};".format(DB_NAME))
            dbcursor.execute(showQueryDetailsStatement)
            print("Select statement successfully executed.")
            queries = dbcursor.fetchall()
            print("Total Queries Found: ", dbcursor.rowcount)
            dbcursor.close()
            conn.close()
            return render_template("viewqueries.html", headings=headings, queries=queries)
         except mysql.connector.Error as e:
            print(e)
            flash("Error: An error occured when attempting to access user bookings.")
            return redirect(url_for("adminpage"))
      else:
         print("Database connection error.")
         flash("Error: Connection error occured when attempting to access your bookings.")
         return redirect(url_for("adminpage"))

#Method to check a user is currently logged in
def checkLoggedIn(): 
   if session.get("CurrentUserID") == None:
      print("User not logged-in, restricting access to this page.")
      abort(403)
   else:
      print("User logged in, allowing access.")

#Method to check whether user is admin
def checkAdmin():
   if session.get("AdminStatus") != "Admin": #Redirects to error page if user is not admin
      print("User not admin, restricting access to this page.")
      abort(403)
   
#Method to check whether its the users first visit to the website, if this returns True then a warning about flask sessions will be given
def checkFirstVisit():
   if session.get("FirstVisit") == None:
      session["FirstVisit"] = True
   else:
      session["FirstVisit"] = False

#Custom errors pages to maintain consistent styling across my website
@app.errorhandler(404)
def error404(error):
   checkFirstVisit()
   return render_template("404error.html"), 404

@app.errorhandler(403)
def error403(error):
   checkFirstVisit()
   return render_template("403error.html"), 403

@app.errorhandler(500)
def error500(error):
   checkFirstVisit()
   return render_template("500error.html"), 500

if __name__ == "__main__":
   app.run(debug = True) #will run the flask app