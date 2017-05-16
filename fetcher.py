import urllib.request
from bs4 import BeautifulSoup
from unidecode import unidecode
import re
import sys
import json
import requests
import base64
import itertools
import sys
import collections
import timeit
import time

import solver


# helper functions for timing 
def _template_func(setup, func):
    """Create a timer function. Used if the "statement" is a callable."""
    def inner(_it, _timer, _func=func):
        setup()
        _t0 = _timer()
        for _i in _it:
            retval = _func()
        _t1 = _timer()
        return _t1 - _t0, retval
    return inner

timeit._template_func = _template_func

timeit.template = """
def inner(_it, _timer{init}):
    {setup}
    _t0 = _timer()
    for _i in _it:
        retval = {stmt}
    _t1 = _timer()
    return _t1 - _t0, retval
"""

sys.setrecursionlimit(100000000)

base_url = "https://www.magiccardmarket.eu"

url = "https://www.magiccardmarket.eu/Products/Singles/Aether+Revolt/Glint-Sleeve+Siphoner"
location_re = re.compile(r"showMsgBox\(this,'Item location: ([^']*)'\)")

def parse_card_table(table, united=False):
    """Parses html table to raw data"""
    res = []

    for row in table.find_all("tr"):
        if "class" in row.attrs:
            continue 

        for tag in row.contents:
            pass


        # table looks differently in all expansion mode
        namerow = 1 if united else 0

        name = row.contents[namerow].span.contents[2].string
        url  = row.contents[namerow].span.contents[2].find("a")["href"]

        location = row.contents[namerow].span.contents[1].span["onmouseover"]
        location = location_re.match(location).group(1)

        price = row.find("td", class_= "st_price").div.div.string

        count = int(row.contents[9 if united else 6].string)

        if not name or not price: 
            continue 

        res += [{
            "name": "" if not name else unidecode(name),
            "price": "" if not price else unidecode(price),
            "url": base_url + url,
            "location": location,
            "count": count
        }]


    return res


ajax_re = re.compile(r"jcp\('([^']*)'\+encodeURI\('([^']*)'\+moreArticlesForm.page.value\+'([^']*)'\)")

def fetch_card(url, united=False):
    print("Fetching", url, file=sys.stderr)
    with urllib.request.urlopen(url) as response:
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')

        allExp = soup.find("a", class_ = "seeAllLink")
        
        if allExp:
            href = "https://www.magiccardmarket.eu" + allExp["href"]
            return fetch_card(href, united=True)


        name = soup.find("h1", class_ = "c-w nameHeader").text

        moreDiv = soup.find("div", id="moreDiv")

        tables = []

        if moreDiv:
            js = moreDiv["onclick"]
            match = ajax_re.search(js)

            head = match.group(1) + match.group(2)
            tail = match.group(3)

            for i in itertools.count():
                newurl = head + str(i) + tail
                
                print("{},".format(i), end=" ", file=sys.stderr)
                sys.stderr.flush()

                # forge AJAX requests

                response = requests.post('https://www.magiccardmarket.eu/iajax.php', data={"args": newurl})
                encoded = response.text[67:-31]
                decoded = base64.b64decode(encoded).decode("utf8")

                if decoded == "0":
                    break

                tables += [BeautifulSoup(decoded, "html.parser")]

            print(file=sys.stderr)

        else:
            tables = [soup.find("table", class_ = "MKMTable fullWidth mt-40").tbody]
        
        res = []
        for table in tables:
            res += parse_card_table(table, united=united)

        return res
    return []

class Cardlist:
    """Methods for fetching cardlists"""
    url_single = "https://www.magiccardmarket.eu/Products/Singles"

    def __init__(self):
        ...

    @classmethod
    def fetch_single(cls, **params):
        response = requests.get(cls.url_single, params)
        print("Fetching", response.url, file=sys.stderr)

        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find("table", class_="MKMTable fullWidth")
        res = []

        for link in table.find_all("a", href= lambda x: x.startswith("/Products")):
            res += [{
                "name": unidecode(link.string), 
                "url" : base_url + link["href"]
            }]

        return res

def fetch_cards(cardlist):
    for card in cardlist:
        card["sellers"] = fetch_card(card["url"])

def fetch_seller(url):
    print("Fetching", url)
    with urllib.request.urlopen(url) as response:
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find("span", typeof="v:Breadcrumb", property="v:title").text
        print ("Name", name, file=sys.stderr)

        url_list = soup.find("ul", class_=re.compile(".*catArticles-list.*"))
        cardlists = [(x.text, x["href"]) for x in url_list.find_all("a")]
        print(cardlists, file=sys.stderr)


class ShippingCost:
    """Class representing shipping cost"""
    url = "https://www.magiccardmarket.eu/Help/Shipping_Costs"

    ShippingDetail = collections.namedtuple("ShippingMethod", ["name", "certified", "max_value", "max_weight", "stamp_price", "price"])

    def __init__(self, src, dst):
        self.source = src
        self.destination = dst

    @classmethod
    def fetch(cls, src, dst):
        response = requests.post(cls.url, {"origin": src, "destination": dst})
        data = response.text

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="MKMTable HelpShippingTable")

        methods = []

        for row in table.tbody.find_all("tr"):
            data = [cell.text for i, cell in enumerate(row.find_all(["th", "td"]))]
            
            if len(data) < 5: continue
            if data[-1] == "": continue

            methods += [cls.ShippingDetail(*data)]
        
        result = cls(src, dst)
        result.methods = methods

        return result

    def groupby(self, f):
        return itertools.groupby(sorted(self.methods, key=f), key=f)

    def get_cheapest(self):
        return [
            
                sorted(data, 
                    key = lambda detail: int(detail.price.split()[0].replace(",", ""))
                )[0]
            
            for weight, data in self.groupby(
                lambda detail: int(detail.max_weight[:-2])
            )
        ]

    def __str__(self):
        return "Shiping({source} -> {destination}: {methods})".format(
            source = self.source,
            destination = self.destination,
            methods = list([x.name for x in self.methods])
        ) 

class ShippingManager:
    """Manager for on demand fetching of shipping costs"""
    def __init__(self):
        self._fetch_mapping()
        self._cached = {}

    def _fetch_mapping(self):
        response = requests.get(ShippingCost.url)
        soup = BeautifulSoup(response.text, "html.parser")

        self._mapping_origin = {
            option.text: option["value"]
            
            for option in soup.find(
                "select", 
                {"name": "origin"}
            ).findChildren()
        }

        self._mapping_origin["Germany"] = "D"

        self._mapping_destination = {
            option.text: option["value"]
            
            for option in soup.find(
                "select", 
                {"name": "destination"}
            ).findChildren()
        }

    def get(self, src, dst):
        if src in self._mapping_origin:
            src = self._mapping_origin[src]
        
        if dst in self._mapping_destination:
            dst = self._mapping_destination[dst]

        target = (src, dst)

        if target not in self._cached:
            print("Fetching shipping {} -> {}".format(src, dst), file=sys.stderr)
            self._cached[target] = ShippingCost.fetch(*target)
            
        return self._cached[target]


manager = ShippingManager()

def fetch_problem(want, manager=manager):
    data = []

    for name, amount in want:
        card_url = Cardlist.fetch_single(name = name)[0]["url"]
        card_sellers = fetch_card(card_url)

        data += [{
            "name": name,
            "url": card_url,
            "sellers": card_sellers,
            "amount": amount
        }]

    return {"want": want, "data": data}



def transform_problem(problem, here, manager=manager):
    """Transforms problem from raw data to constraints and variables"""

    want = problem["want"]
    data = problem["data"]

    class Varlist:
        def __init__(self):
            self.location = "UNK"
            self.variables = []

        def __str__(self):
            return "Varlist(loc: {}, vars: {})".format(self.location, self.variables)

        def __repr__(self):
            return str(self)


    vars = solver.Variables()

    objective = []
    constraints = []

    sellers = collections.defaultdict(Varlist) 

    i = 0

    for card in data:
        total = []

        for seller in card["sellers"]:
            seller["cardname"] = card["name"]
            x = vars.int("x", seller)

            name = seller["name"]
            sellers[name].location = seller["location"]
            sellers[name].variables += [x]

            constraints += [solver.Constraint("S" + str(i), "L", 1 * x, rhs = seller["count"])]
            objective += [(seller["price"].split()[0].replace(",", "") * x)]
            total += [1 * x]

            i += 1

        constraints += [solver.Constraint("W" + str(i), "E", *total, rhs=card["amount"])]



    card_weight = 5

    BIG = 9999

    for name, varlist in sellers.items():
        variables = varlist.variables
        variables = [-1 * var for var in variables]

        loc  = varlist.location

        shipping = manager.get(loc, here)

        last_price = 0
        last_count = 1

        for cost in shipping.get_cheapest():
            price = int(cost.price.split()[0].replace(",", ""))

            y = vars.bool("y")

            objective += [((price - last_price) * y)]

            constraints += [solver.Constraint("C" + str(i), "L", last_count * y , *variables, rhs=0)]
            constraints += [solver.Constraint("B" + str(i), "G", BIG * y , *variables, rhs= 1 - last_count)]

            last_count = int(cost.max_weight.split()[0]) // card_weight + 1
            last_price = price

            i += 1

    return ([solver.Constraint("R1", "N", *objective)] + constraints, vars)


def solve(want, country, lpsolver, file, problem=None):
    """Solves and prints the sollution"""
    
    if problem is None:
        problem = fetch_problem(want, country)
    
    problem = transform_problem(problem, country)
    solver.write_mps(problem, file)

    print("Running {} ... ".format(type(lpsolver).__name__), end="", file=sys.stderr)

    timing = timeit.Timer(lambda: lpsolver.solve_mps(file))
    time, res = timing.timeit(number=1)

    print(res[0], file=sys.stderr)
    print("\n{}\n===============\n    time: {:>40}\n    sol : {:>40}\n".format(type(lpsolver).__name__, time, res[0]))

    sol, vars = res
    _, names = problem

    for name, val in vars:
        key = names.get_key(name)
        
        if not key:
            continue

        print("{:20} from {:30}: {:2}x {:5}".format(key["cardname"], key["name"], str(val), key["price"]), file=sys.stderr)
