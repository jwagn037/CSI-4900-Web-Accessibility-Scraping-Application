import pickle
    
def pickle_save(loc, data):
    with open(loc, 'wb') as file:
        pickle.dump(data, file)

def pickle_load(loc):
    with open(loc, 'rb') as file:
        return pickle.load(file)

def txt_to_dictionary(loc):
    with open(loc, 'r') as file:
        new_dict = {}
        n = 0
        for line in file:
            if (line.startswith("#")):
                continue
            
            line_list = line.strip().split()
            domain = line_list[1]
            ip = line_list[0]
            
            new_dict[domain] = ip
    return new_dict

def get_domain_dict(list_name):
    if (list_name == "adservers"):
        try:
            return pickle_load("domain_lists/adservers.pickle")
        except:
            domain_dict = txt_to_dictionary("domain_lists/adservers.txt")
            pickle_save("domain_lists/adservers.pickle", domain_dict)
            return domain_dict
    elif (list_name == "allowlist"):
        try:
            return pickle_load("domain_lists/allowlist.pickle")
        except:
            domain_dict = txt_to_dictionary("domain_lists/allowlist.txt")
            pickle_save("domain_lists/allowlist.pickle", domain_dict)
            return domain_dict
    elif (list_name == "blocklist"):
        try:
            return pickle_load("domain_lists/blocklist.pickle")
        except:
            domain_dict = txt_to_dictionary("domain_lists/blocklist.txt")
            pickle_save("domain_lists/blocklist.pickle", domain_dict)
            return domain_dict
    else:
        print(Exception("Invalid argument for get_domain_dict: ", list_name))
        return Exception("Invalid argument for get_domain_dict: ", list_name)