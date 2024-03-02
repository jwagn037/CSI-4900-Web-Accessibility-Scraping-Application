import time
import domain_parser

# Test function for domain_parser
# On my machine with trials=1000, we are usually in the ballpark of
# 30 seconds for the first test; 10 seconds for the second.
# (i.e. reading the dictionary from a pickle is ~66% faster than building 
# it from txt)
def test_domain_parser(trials=1000):
    print("Running test")
    # --------------

    loc = "domain_lists/adservers.txt"
    start = time.time()
    for i in range (0,trials):
        domain_dict = domain_parser.txt_to_dictionary(loc)
    end = time.time()
    print("Domain dict built in " + str(end - start) + " seconds for trials=" + str(trials))
    # --------------
    
    loc = "domain_lists/adserver.pickle"
    domain_parser.pickle_save(loc, domain_dict)
    # --------------
    
    start = time.time()
    for i in range (0,trials):
        domain_dict = domain_parser.pickle_load(loc)
    end = time.time()
    print("Domain dict pickle read in " + str(end - start) + " seconds for trials=" + str(trials))
    # --------------

    print("Test concluded")

def build_allowlists_and_blocklists():
    adserver_dict = domain_parser.get_domain_dict("adservers")
    blocklist_dict = domain_parser.get_domain_dict("blocklist")
    allowlist_dict = domain_parser.get_domain_dict("allowlist")