from flask import g
from datetime import datetime, timezone

#####################################################################################################################
################################################## HELPER METHODS ###################################################
#####################################################################################################################

# Returns a timestamp with the current date and time, without timezone
def _current_timestamp():
    dt_obj_w_tz = datetime.now() 
    dt_obj_w_tz = dt_obj_w_tz.replace(tzinfo=timezone.utc)
    dt_obj_wo_tz = dt_obj_w_tz.replace(tzinfo=None) # Read as "DateTime object without timezone"
    return dt_obj_wo_tz

# Searches webpage_src for a particular URL.
# Returns the webpage_json_id of a requested webpage, or False if it is not indexed.
# If it is not indexed, then its JSON isn't in the database.
def _get_webpage_id(url):
    try:
        g.cur.execute('SELECT webpage_id FROM webpage_src WHERE webpage_url=(%s);', (url,))
        webpage_json_id = g.cur.fetchone()[0]
        return webpage_json_id
    except Exception as e:
        # The webpage isn't cached, or the DB failed for some reason
        print("_get_webpage_id() failed. The webpage may not be cached, or the database failed:", e)
        return False

# Searches webpage_src for a particular URL.
# Returns the webpage_src_id if it exists, or False if it is not indexed.
def _get_webpage_src_id(url):
    try:
        g.cur.execute('SELECT webpage_src_id FROM webpage_src WHERE webpage_url=(%s);', (url,))
        webpage_src_id = g.cur.fetchone()[0]
        return webpage_src_id
    except Exception as e:
        # The webpage isn't cached, or the DB failed for some reason
        print("_get_webpage_src_id failed. The webpage may not be cached, or the database failed:", e)
        return False

# Searches webpage_json to determine if a particular ID exists in the table.
# Returns webpage_id if it does exist, and False if it does not.
# If it does not exist in webpage_json, it could still exist in webpage_src. This would mean
# the webpage was cached at some point and there was a "shallow" deletion on the JSON data.
def _webpage_json_exists(webpage_json_id):
    try:
        g.cur.execute('SELECT * FROM webpage_json WHERE webpage_id=(%s)', (webpage_json_id,))
        webpage_json_id = g.cur.fetchone()[0]
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
def _webpage_ever_cached(url):
    webpage_json_id = _get_webpage_id(url)
    if (webpage_json_id == False): # webpage_src entry DNE; webpage_json entry has UNKNOWN STATUS
        print("NAN: DB table webpage_src does not contain url=",url)
        return 3
    
    # This FAILS, for some reason, so the system won't detect an existing webpage_json entry
    if (_webpage_json_exists(webpage_json_id) == False): # webpage_src entry EXISTS; webpage_json entry DNE
        print("NAN: DB table webpage_src does not contain an entry for webpage_id=",webpage_json_id)
        return 2
    
    return 1 # webpage_src entry EXISTS; webpage_json entry EXISTS

#####################################################################################################################
################################################ INSERT OPERATIONS ##################################################
#####################################################################################################################

# Inserts a row to webpage_json and returns webpage_ID
def _insert_webpage_json(title, author, publish_date, timestamp):
    g.cur.execute('INSERT INTO webpage_json (title, author, publish_date, cached_at) '
                'VALUES (%s, %s, %s, %s) RETURNING webpage_id',
                (title, author, publish_date, timestamp))
    inserted_id = g.cur.fetchone()[0]
    return inserted_id

# Inserts a row to webpage_src and returns webpage_src_id
def _insert_webpage_src(url, webpage_json_id):
    g.cur.execute('INSERT INTO webpage_src (webpage_id, webpage_url) '
                'VALUES (%s, %s) RETURNING webpage_id',
                (webpage_json_id,url))
    inserted_id = g.cur.fetchone()[0]
    return inserted_id

# Inserts a row to element and returns element_id
def _insert_element(webpage_id, element_index):
    g.cur.execute('INSERT INTO element (webpage_id, element_index) '
                'VALUES (%s, %s) RETURNING element_id',
                (webpage_id, element_index))
    inserted_id = g.cur.fetchone()[0]
    return inserted_id

# Inserts a row to text_element and returns element_id
def _insert_text_element(element_id, element_type, element_data):
    g.cur.execute('INSERT INTO text_element (element_id, element_type, element_data) '
                'VALUES (%s, %s, %s) RETURNING element_id',
                (element_id, element_type, element_data))
    inserted_id = g.cur.fetchone()[0]  
    return inserted_id

# Inserts a row to image_element and returns element_id
def _insert_image_element(element_id, caption, alt_text, alt_text_type, element_data):
    g.cur.execute('INSERT INTO image_element (element_id, caption, alt_text, alt_text_type, element_data) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING element_id',
                (element_id, caption, alt_text, alt_text_type, element_data))
    inserted_id = g.cur.fetchone()[0]  
    return inserted_id

# Inserts a row to request_record and returns request_record_id
def _insert_request_record(url, request_type):
    webpage_src_id = _get_webpage_src_id(url)
    time_requested = _current_timestamp()
    g.cur.execute('INSERT INTO request_record (webpage_src_id, time_requested, request_type) '
                'VALUES (%s, %s, %s) RETURNING request_record_id',
                (webpage_src_id, time_requested, request_type))
    inserted_id = g.cur.fetchone()[0]  
    return inserted_id

#####################################################################################################################
################################################ SELECT OPERATIONS ##################################################
#####################################################################################################################
def _get_text_elements(url):
    g.cur.execute("""
        SELECT e.element_index, te.element_type, te.element_data
        FROM webpage_src ws
        JOIN webpage_json wj ON ws.webpage_id = wj.webpage_id
        JOIN "element" e ON e.webpage_id = ws.webpage_id
        JOIN text_element te ON te.element_id = e.element_id
        WHERE ws.webpage_url = %s;
    """, (url,))
    result = g.cur.fetchall()
    return result

def _get_image_elements(url):
    g.cur.execute("""
        SELECT e.element_index, ie.caption, ie.alt_text, ie.alt_text_type, ie.element_data
        FROM webpage_src ws
        JOIN webpage_json wj ON ws.webpage_id = wj.webpage_id
        JOIN "element" e ON e.webpage_id = ws.webpage_id
        JOIN image_element ie ON ie.element_id = e.element_id
        WHERE ws.webpage_url = %s;
    """, (url,))
    result = g.cur.fetchall()
    return result

def _get_webpage_info(url):
    g.cur.execute("""
        SELECT wj.title, wj.author, wj.publish_date, wj.cached_at
        FROM webpage_src ws
        JOIN webpage_json wj ON ws.webpage_id = wj.webpage_id
        WHERE ws.webpage_url = %s;
    """, (url,))
    result = g.cur.fetchone()
    return result


#####################################################################################################################
################################################## CRUD OPERATIONS ##################################################
#####################################################################################################################

# CREATE operation:
# Given a url and json, cache a webpage in the DB.
# with_src is a flag to determine whether we should create an entry in webpage_src for this
def _create_json_cache(url, json, new_src_index):
    title = json['title']
    author = json['author']
    publish_date = json['date']
    content = json['content']
    
    insertion_timestamp = _current_timestamp()
    webpage_json_id = _insert_webpage_json(title, author, publish_date, insertion_timestamp)
    
    if (new_src_index):
        webpage_src_id = _insert_webpage_src(url, webpage_json_id)
    
    index = 0
    for item in content:
        if (len(item['text'].strip())==0): # Don't cache empty data. It's rude.
            continue
        
        item_type = item['type']
        element_id = _insert_element(webpage_json_id,index)
        if (item['type'] == 'img'):
            caption=item['caption']
            alt_text=item['alt_text']
            alt_text_type=item['alt_text_type']
            element_data=item['text']
            img_element_id = _insert_image_element(element_id, caption, alt_text, alt_text_type, element_data)
        else:
            element_data=item['text'].strip()
            text_element_id = _insert_text_element(element_id,item_type,element_data)
        index += 1
    
    return webpage_json_id

# DELETE operation:
# Clears the json data stored for a specific webpage.
# Leaves its index in webpage_src intact to maintain records associated with webpage_json.
def _shallow_delete_json_cache(url):
    webpage_id = _get_webpage_id(url)
    try:
        g.cur.execute('DELETE FROM webpage_json WHERE webpage_id = (%s);', (webpage_id,))
        return True
    except Exception as e:
        print("Could not delete article from WASA_DB: ", e)
        return False

# DELETE operation:
# Clears the json data stored for a specific webpage.
# This INCLUDES webpage_src and request_record entries.
def _deep_delete_json_cache(url):
    # This function has problems with orphaned rows in webpage_json
    webpage_id = _get_webpage_id(url)
    if (webpage_id != False):
        _shallow_delete_json_cache(url)
    
    try:
        g.cur.execute('DELETE FROM webpage_src WHERE webpage_url = (%s);', (url,))
        return True
    except Exception as e:
        print("Could not delete article from WASA_DB: ", e)
        return False

# DELETE operation:
# Clear ALL of the data in the database.
def _total_wipe():
    try:
        g.cur.execute('TRUNCATE TABLE webpage_json CASCADE;')
        return True
    except Exception as e:
        print("Could not wipe WASA_DB:", e)
        return False

# Updates the entry in webpage_src contain
def _update_webpage_src(url, new_webpage_id):
    try:
        g.cur.execute('UPDATE webpage_src SET webpage_id=(%s) WHERE webpage_url=(%s);', (new_webpage_id,url))
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

# Attempts to read from the databse. Returns webpage JSON on success, or False an a failure.
# READ operation: given a url, read a webpage from the DB.
def read_cache_request(url):
    # Premature exit if the page isn't cached
    in_cache = _get_webpage_id(url)
    if (in_cache == False):
        return False
    
    webpage_info = _get_webpage_info(url)
    last_cached_at = webpage_info[3] # can use this to deny the read request
    
    json_article = {}
    json_article['title'] = webpage_info[0]
    json_article['author'] = webpage_info[1]
    json_article['date'] = webpage_info[2]
    content = []
    
    text_elements = _get_text_elements(url)
    image_elements = _get_image_elements(url)
    elements = text_elements + image_elements
    elements = sorted(elements, key=lambda item: item[0])
    
    content = []
    
    for item in elements:
        item_json ={}
        if (len(item)==3):     
            item_json['type'] = item[1]
            item_json['text'] = item[2]
        if (len(item)==5):
            item_json['type'] = 'img'
            item_json['caption'] = item[1]
            item_json['alt_text'] = item[2]
            item_json['alt_text_type'] = item[3]
            item_json['text'] = item[4]
        content.append(item_json)
        
    json_article['content'] = content
    _insert_request_record(url, "READ")
    return json_article

# Attempts to write to the database. Returns True on success, or False on a failure.
# WRITE operation: from the database's POV, we are performing some combination of delete, insert, and update.
def write_cache_request(url, json):
    # Check if the webpage has been cached before
    print("WCR1")
    webpage_cache_status = _webpage_ever_cached(url)
    
    if (webpage_cache_status==1): #webpage_src entry EXISTS; webpage_json entry EXISTS
        print("WCR2")
        _shallow_delete_json_cache(url)
        new_webpage_json_id = _create_json_cache(url, json, new_src_index=False)
        _update_webpage_src(url, new_webpage_json_id)
        _insert_request_record(url, "UPDATE")
        return json
    elif (webpage_cache_status==2): #webpage_src entry EXISTS; webpage_json entry DNE
        print("WCR3")
        new_webpage_json_id = _create_json_cache(url, json, new_src_index=False)
        print("WCR3.1")
        _update_webpage_src(url, new_webpage_json_id)
        print("WCR3.2")
        _insert_request_record(url, "UPDATE")
        return False
    elif (webpage_cache_status==3): #webpage_src entry DNE; webpage_json entry has UNKNOWN STATUS (if out delete operations are sound, then webpage_json entry PROBABLY DNE)
        print("WCR4")
        _create_json_cache(url, json, new_src_index=True)
        _insert_request_record(url, "CREATE")
        return False
    else:
        return False

# Clears the entire cache database.
def delete_cache_request():
    _total_wipe()