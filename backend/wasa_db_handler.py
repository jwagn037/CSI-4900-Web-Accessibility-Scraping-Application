import os
import psycopg2
from datetime import datetime, timezone

# Connect to WASA_DB
conn = psycopg2.connect(
        host="localhost",
        database="WASA_DB",
        user='WASA_admin',
        password='admin')

# Open a cursor to perform database operations
cur = conn.cursor()

#####################################################################################################################
################################################## HELPER METHODS ###################################################
#####################################################################################################################

# Returns a timestamp with the current date and time, without timezone
def current_timestamp():
    dt_obj_w_tz = datetime.now() 
    dt_obj_w_tz = dt_obj_w_tz.replace(tzinfo=timezone.utc)
    dt_obj_wo_tz = dt_obj_w_tz.replace(tzinfo=None) # Read as "DateTime object without timezone"
    return dt_obj_wo_tz

# Searches webpage_src for a particular URL.
# Returns the webpage_json_id of a requested webpage, or False if it is not indexed.
# If it is not indexed, then its JSON isn't in the database.
def get_webpage_id(url, cur=cur):
    try:
        cur.execute('SELECT webpage_id FROM webpage_src WHERE webpage_url=(%s);', (url,))
        webpage_json_id = cur.fetchone()[0]
        return webpage_json_id
    except Exception as e:
        # The webpage isn't cached, or the DB failed for some reason
        print("get_webpage_id() failed. The webpage may not be cached, or the database failed:", e)
        return False

# Searches webpage_json to determine if a particular ID exists in the table.
# Returns webpage_id if it does exist, and False if it does not.
# If it does not exist in webpage_json, it could still exist in webpage_src. This would mean
# the webpage was cached at some point and there was a "shallow" deletion on the JSON data.
def webpage_json_exists(webpage_json_id, cur=cur):
    try:
        cur.execute('SELECT * FROM webpage_json WHERE webpage_id=(%s)', (webpage_json_id,))
        webpage_json_id = cur.fetchone()[0]
        return webpage_json_id
    except Exception as e:
        # The webpage isn't cached, or the DB failed for some reason
        print("webpage_json_exists() error:", e)
        return False

# Combines get_webpage_id and webpage_json_exists to determine if a webpage was ever cached.
# Returns an integer indicating whether a webpage was ever cached. Return values:
# 1 -> webpage_src entry EXISTS; webpage_json entry EXISTS
# 2 -> webpage_src entry EXISTS; webpage_json entry DNE
# 3 -> webpage_src entry DNE; webpage_json entry has UNKNOWN STATUS (if out delete operations are sound, then webpage_json entry PROBABLY DNE)
def webpage_ever_cached(url):
    webpage_json_id = get_webpage_id(url)
    if (webpage_json_id == False): # webpage_src entry DNE; webpage_json entry has UNKNOWN STATUS
        print("NAN: DB table webpage_src does not contain url=",url)
        return 3
    
    # This FAILS, for some reason, so the system won't detect an existing webpage_json entry
    if (webpage_json_exists(webpage_json_id) == False): # webpage_src entry EXISTS; webpage_json entry DNE
        print("NAN: DB table webpage_src does not contain an entry for webpage_id=",webpage_json_id)
        return 2
    
    return 1 # webpage_src entry EXISTS; webpage_json entry EXISTS

#####################################################################################################################
################################################ INSERT OPERATIONS ##################################################
#####################################################################################################################

# Inserts a row to webpage_json and returns webpage_ID
def insert_webpage_json(title, author, publish_date, timestamp, cur=cur):
    cur.execute('INSERT INTO webpage_json (title, author, publish_date, cached_at) '
                'VALUES (%s, %s, %s, %s) RETURNING webpage_id',
                (title, author, publish_date, timestamp))
    inserted_id = cur.fetchone()[0]
    return inserted_id

# Inserts a row to webpage_src and returns webpage_src_id
def insert_webpage_src(url, webpage_json_id, cur=cur):
    cur.execute('INSERT INTO webpage_src (webpage_id, webpage_url) '
                'VALUES (%s, %s) RETURNING webpage_id',
                (webpage_json_id,url))
    inserted_id = cur.fetchone()[0]
    return inserted_id

# Inserts a row to element and returns element_id
def insert_element(webpage_id, element_index, cur=cur):
    cur.execute('INSERT INTO element (webpage_id, element_index) '
                'VALUES (%s, %s) RETURNING element_id',
                (webpage_id, element_index))
    inserted_id = cur.fetchone()[0]
    return inserted_id

# Inserts a row to text_element and returns element_id
# Inserts a row to element and returns element_id
def insert_text_element(element_id, element_type, element_data, cur=cur):
    cur.execute('INSERT INTO text_element (element_id, element_type, element_data) '
                'VALUES (%s, %s, %s) RETURNING element_id',
                (element_id, element_type, element_data))
    inserted_id = cur.fetchone()[0]  
    return inserted_id

#####################################################################################################################
################################################ SELECT OPERATIONS ##################################################
#####################################################################################################################
def get_text_elements(url):
    cur.execute("""
        SELECT e.element_index, te.element_type, te.element_data
        FROM webpage_src ws
        JOIN webpage_json wj ON ws.webpage_id = wj.webpage_id
        JOIN "element" e ON e.webpage_id = ws.webpage_id
        JOIN text_element te ON te.element_id = e.element_id
        WHERE ws.webpage_url = %s;
    """, (url,))
    result = cur.fetchall()
    return result

def get_image_elements(url):
    cur.execute("""
        SELECT e.element_id, ie.caption, ie.alt_text, ie.alt_text_type, ie.element_data
        FROM webpage_src ws
        JOIN webpage_json wj ON ws.webpage_id = wj.webpage_id
        JOIN "element" e ON e.webpage_id = ws.webpage_id
        JOIN image_element ie ON ie.element_id = e.element_id
        WHERE ws.webpage_url = %s;
    """, (url,))
    result = cur.fetchall()
    return result

def get_webpage_info(url):
    cur.execute("""
        SELECT wj.title, wj.author, wj.publish_date, wj.cached_at
        FROM webpage_src ws
        JOIN webpage_json wj ON ws.webpage_id = wj.webpage_id
        WHERE ws.webpage_url = %s;
    """, (url,))
    result = cur.fetchone()
    return result


#####################################################################################################################
################################################## CRUD OPERATIONS ##################################################
#####################################################################################################################

# CREATE operation:
# Given a url and json, cache a webpage in the DB.
# with_src is a flag to determine whether we should create an entry in webpage_src for this
def create_json_cache(url, json, new_src_index):
    title = json['title']
    author = json['author']
    publish_date = json['date']
    content = json['content']
    
    insertion_timestamp = current_timestamp()
    webpage_json_id = insert_webpage_json(title, author, publish_date, insertion_timestamp)
    
    if (new_src_index):
        webpage_src_id = insert_webpage_src(url, webpage_json_id)
    
    index = 0
    for item in content:
        if (len(item['text'].strip())==0): # Don't cache empty data. It's rude.
            continue
        
        item_type = item['type']
        element_id = insert_element(webpage_json_id,index,cur)
        if (item['type'] == 'img'):
            print("image element")
        else:
            element_data=item['text'].strip()
            text_element_id = insert_text_element(element_id,item_type,element_data,cur)
        index += 1
    
    return webpage_json_id


# DELETE operation:
# Clears the json data stored for a specific webpage.
# This INCLUDES webpage_src and request_record entries.
def deep_delete_json_cache(url):
    # This function has problems with orphaned rows in webpage_json
    webpage_id = get_webpage_id(url)
    if (webpage_id != False):
        shallow_delete_json_cache(url)
    
    try:
        cur.execute('DELETE FROM webpage_src WHERE webpage_url = (%s);', (url,))
        return True
    except Exception as e:
        print("Could not delete article from WASA_DB: ", e)
        return False

# DELETE operation:
# Clears the json data stored for a specific webpage.
# Leaves its index in webpage_src intact to maintain records associated with webpage_json.
def shallow_delete_json_cache(url):
    webpage_id = get_webpage_id(url)
    try:
        cur.execute('DELETE FROM webpage_json WHERE webpage_id = (%s);', (webpage_id,))
        return True
    except Exception as e:
        print("Could not delete article from WASA_DB: ", e)
        return False

# DELETE operation:
# Clear ALL of the data in the database.
def total_wipe():
    try:
        cur.execute('TRUNCATE TABLE webpage_json CASCADE;')
        return True
    except Exception as e:
        print("Could not wipe WASA_DB:", e)
        return False

#####################################################################################################################
################################################## CRUD OPERATIONS ##################################################
#####################################################################################################################

# Updates the entry in webpage_src contain
def update_webpage_src(url, new_webpage_id):
    try:
        cur.execute('UPDATE webpage_src SET webpage_id=(%s) WHERE webpage_url=(%s);', (new_webpage_id,url))
        return True
    except Exception as e:
        print("Could not update webpage_src for url:", url, e)
        return False

######################################################################################################################
#################################################### "MAIN" CODE #####################################################
######################################################################################################################
# These are the only methods an external module is "allowed" to call. The database handler is solely responsible for #
# database logic. The handler chooses whether a cache should be returned. The caller is at the behest of the handler,#
# not the other way around.                                                                                          #
######################################################################################################################

# Attempts to read from the databse.
# Returns webpage JSON on success, or False an a failure.
# READ operation:
# Given a url, read a webpage from the DB.
def read_cache_request(url, cur=cur):
    # Premature exit if the page isn't cached
    in_cache = get_webpage_id(url, cur=cur)
    if (in_cache == False):
        return False
    
    webpage_info = get_webpage_info(url)
    last_cached_at = webpage_info[3] # can use this to deny the read request
    
    json_article = {}
    json_article['title'] = webpage_info[0]
    json_article['author'] = webpage_info[1]
    json_article['date'] = webpage_info[2]
    content = []
    
    text_elements = get_text_elements(url)
    image_elements = get_image_elements(url)
    elements = text_elements + image_elements
    
    content = []
    
    for item in elements:
        if (len(item)==3):            
            item_json ={}
            item_json['type'] = item[1]
            item_json['text'] = item[2]
        if (len(item)==5):
            # save image element
            pass
        content.append(item_json)
        
    json_article['content'] = content
    return json_article

# Attempts to write to the database.
# Returns True on success, or False on a failure.
def write_cache_request(url, json):
    # Check if the webpage has been cached before
    print("WCR1")
    webpage_cache_status = webpage_ever_cached(url)
    
    if (webpage_cache_status==1): #webpage_src entry EXISTS; webpage_json entry EXISTS
        print("WCR2")
        shallow_delete_json_cache(url)
        new_webpage_json_id = create_json_cache(url, json, new_src_index=False)
        update_webpage_src(url, new_webpage_json_id)
        return json
    elif (webpage_cache_status==2): #webpage_src entry EXISTS; webpage_json entry DNE
        print("WCR3")
        new_webpage_json_id = create_json_cache(url, json, new_src_index=False)
        print("WCR3.1")
        update_webpage_src(url, new_webpage_json_id)
        print("WCR3.2")
        return False
    elif (webpage_cache_status==3): #webpage_src entry DNE; webpage_json entry has UNKNOWN STATUS (if out delete operations are sound, then webpage_json entry PROBABLY DNE)
        print("WCR4")
        create_json_cache(url, json, new_src_index=True)
        return False
    else:
        return False

# Clears the entire cache database.
def delete_cache_request():
    total_wipe()

######################################################################################################################
######################################################################################################################
######################################################################################################################
################################### IMPORTS ###################################
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
from trafilatura import extract
import validators
import hashlib
import os


################################### FLASK ###################################


def parse_response(html):
    json_default = "{}" ## default empty JSON
    
    # minimal parsing:
    tags = ['h1','h2','h3','h4','h5','h6', 'p', 'ul']
    soup = BeautifulSoup(html, 'html.parser')
    result = soup.find_all(tags)
    print(type(result))
    
    soup.findAll(text=True)
    text = extract(html, favor_precision=True)
    for item in result:
        if (item.text not in text):
            result.remove(item)
    return write_json(result)

# Handles the complex business logic of getting HTML from a URL.
# Returns HTML. Variable html.type()=str().
def get_url_html(url, directory='pseudocache'):
    
    # Can't read from cache. Make request.
    print("Request:", url)
    response = requests.get(url)
    html = response.text
    
    return str(html)
    
    # Handles complex business logic for different HTML parsing approaches.
    # mode == 0: BS4 parsing
    # mode == 1: Trafilatura parsing
    # Defaults to BS4 parsing.

    # Builds a JSON object with the format provided in the wiki.
    # Needs a ResultSet for text. The rest can be blank, or strings.
def write_json(text, title='',author='',date=''):
    json_article = {}
    json_article['title'] = title
    json_article['author'] = author
    json_article['date'] = date
    content = []
    
    for item in text:
        item_json ={}
        item_json['type'] = item.name
        item_json['text'] = item.text
        content.append(item_json)
        
    json_article['content'] = content
    return json_article


######################################## TEST URL 1 ########################################
test_url = "https://www.cbc.ca/news/canada/edmonton/westlock-alta-residents-vote-to-get-rid-of-town-s-rainbow-crosswalk-in-plebiscite-1.7120498"
request_json = parse_response(get_url_html(test_url))

# print(request_json)
# print(type(request_json))

print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("START TEST 1!\n")
print("Clear DB")
delete_cache_request()

print("Try to read empty DB")
print(read_cache_request(test_url))
print("WEC status BEFORE add",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to add the item.")
write_cache_request(test_url, request_json)
print("Try to read the item:",type(read_cache_request(test_url)))
print("WEC status after add",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nShallow delete the item")
print("Try to read the item:",type(read_cache_request(test_url)))
print("WEC status after add, delete:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to add the item back.")
write_cache_request(test_url, request_json)
print("WEC status after add, delete, add:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nDEEP delete the item")
print("WEC status DEEP DELETE:",webpage_ever_cached(test_url))
print("Try to read the item:",type(read_cache_request(test_url)))
print("Try to add the item back.")
print("WEC status DEEP DELETE and ADD:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to read the item:",type(read_cache_request(test_url)))
print("Try to add the item back.")
write_cache_request(test_url, request_json)
print("Try to read the item:",type(read_cache_request(test_url)))

######################################## TEST URL 2 ########################################
test_url = "https://stackoverflow.com/questions/71531795/postgresql-restart-serial-primary-key"
request_json = parse_response(get_url_html(test_url))

# print(request_json)
# print(type(request_json))

print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("START TEST 2!\n")

print("Try to read empty DB")
print(read_cache_request(test_url))
print("WEC status BEFORE add",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to add the item.")
write_cache_request(test_url, request_json)
print("Try to read the item:",type(read_cache_request(test_url)))
print("WEC status after add",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nShallow delete the item")
print("Try to read the item:",type(read_cache_request(test_url)))
print("WEC status after add, delete:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to add the item back.")
write_cache_request(test_url, request_json)
print("WEC status after add, delete, add:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nDEEP delete the item")
print("WEC status DEEP DELETE:",webpage_ever_cached(test_url))
print("Try to read the item:",type(read_cache_request(test_url)))
print("Try to add the item back.")
print("WEC status DEEP DELETE and ADD:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to read the item:",type(read_cache_request(test_url)))
print("Try to add the item back.")
write_cache_request(test_url, request_json)
print("Try to read the item:",type(read_cache_request(test_url)))


######################################## TEST URL 3 ########################################
test_url = "https://nationalpost.com/news/canada/electric-school-buses-finally-make-headway-but-hurdles-still-stand"
request_json = parse_response(get_url_html(test_url))

# print(request_json)
# print(type(request_json))

print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("#########################################################################################")
print("START TEST 3!\n")

print("Try to read empty DB")
print(read_cache_request(test_url))
print("WEC status BEFORE add",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to add the item.")
write_cache_request(test_url, request_json)
print("Try to read the item:",type(read_cache_request(test_url)))
print("WEC status after add",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nShallow delete the item")
print("Try to read the item:",type(read_cache_request(test_url)))
print("WEC status after add, delete:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to add the item back.")
write_cache_request(test_url, request_json)
print("WEC status after add, delete, add:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nDEEP delete the item")
print("WEC status DEEP DELETE:",webpage_ever_cached(test_url))
print("Try to read the item:",type(read_cache_request(test_url)))
print("Try to add the item back.")
print("WEC status DEEP DELETE and ADD:",webpage_ever_cached(test_url))
print("#########################################################################################")


print("\nTry to read the item:",type(read_cache_request(test_url)))
print("Try to add the item back.")
write_cache_request(test_url, request_json)
print("Try to read the item:",type(read_cache_request(test_url)))





conn.commit()

cur.close()
conn.close()

# https://stackoverflow.com/questions/48021238/how-to-use-after-request-in-flask-to-close-database-connection-and-python
# info for global database connection handling...