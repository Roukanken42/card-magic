import itertools 
import collections
import subprocess
import os
import re

class Constraint:  
    """Constraint of a LP problem"""
    def __init__(self, name, type, *terms, rhs=None):
        self.name = name
        self.type = type
        self.terms = terms
        self.rhs = rhs

    def __str__(self):
        res = ""
        
        if self.name:
            res += self.name + ": "

        res += " ".join([str(term) for term in self.terms])

        if self.rhs is not None:
            res += " " +self.type + " " + str(self.rhs)

        return res

class Term:
    def __init__(self, const, var):
        self.const = const
        self.var = var

    def __str__(self):
        return ("+" if self.const >= 0 else "") + str(self.const) + " * " + str(self.var)


class Variable():
    """Variable class for easy access"""
    def __init__(self, name):
        self.name = name
        # self.type = type

    def __str__(self):
        return self.name

    def __mul__(self, other):
        return Term(int(other), self)

    def __rmul__(self, other):
        return self * other

class Variables:
    """Variable repository"""
    def __init__(self):
        self.data = {}
        self.by_type = collections.defaultdict(list)
        self.count = collections.defaultdict(lambda: itertools.count(1))

    def new(self, type, prefix, key=""):
        num = next(self.count[prefix])
        name = prefix + str(num)

        self.by_type[type] += [name]
        self.data[name] = key

        return Variable(name)
    
    def int(self, prefix, key=""):
        return self.new("int", prefix, key)

    def bool(self, prefix, key=""):
        return self.new("bool", prefix, key)

    def get_by_type(self, type):
        return self.by_type[type]

    def get_ints(self):
        return self.get_by_type("int")

    def get_bools(self):
        return self.get_by_type("bool")

    def get_key(self, name):
        return self.data[name]

    def __len__(self):
        return sum([len(x) for x in self.by_type.values()])



def write_mps(lp, file):
    """Writes problem as mps into a file"""
    out = open(file, "w")
    out.write("NAME          OPTIMIZE\n")
    out.write("ROWS\n")

    constraints, vars = lp

    for constraint in constraints:
        if constraint.type:
            out.write(" {}  {}\n".format(constraint.type, constraint.name))


    mapping = collections.defaultdict(list)

    for constraint in constraints:
        for term in constraint.terms:
            mapping[str(term.var)] += [(constraint.name, term.const)]

    out.write("COLUMNS")

    for var, data in mapping.items():
        for i, (name, val) in enumerate(data):
            if i % 2 == 0:
                out.write("\n    {:<8}".format(var))
            
            # out.write("  {:<8}  {} ".format(name, "{:.15f}".format(val)[:12]))
            out.write("  {:<8}  {:12} ".format(name, val))

    out.write("\nRHS")

    for i, constraint in enumerate([cons for cons in constraints if cons.rhs is not None]):
        if i%2 == 0:
            out.write("\n    RHS1    ")

        out.write("  {:8}  {:12} ".format(constraint.name, constraint.rhs))    

    out.write("\nBOUNDS\n")

    for int in vars.get_ints():
        out.write(" LI BND1      {:8}  {:12}\n".format(int, 0))      

    for int in vars.get_bools():
        out.write(" BV BND1      {:8}\n".format(int))      


    out.write("ENDATA")



# Solver mappings and parsers

class Gurobi:
    cmd = "gurobi_cl"

    def __init__(self):
        pass

    def solve_mps(self, file):
        sol = os.path.splitext(file)[0] + ".sol"
        gurobi = subprocess.Popen([self.cmd, "Resultfile=" + sol, file], stdout=subprocess.PIPE)
        out, err = gurobi.communicate(b"")  

        vars = []

        _, sol_line, *lines = open(sol).readlines()

        result = round((float(sol_line.split("= ")[1])))

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            var, value = line.split()
            value = round(float(value))

            if value:
                vars += [(var, value)]

        return (result, vars)



class Lp_solve:
    cmd = "lp_solve"
    var_re = re.compile(r"([a-z0-9]+) +([0-9]+)")
    value_re = re.compile(r"Value of objective function: ([0-9.]+)")

    def __init__(self, timeout=None):
        self.timeout = timeout

    def solve_mps(self, file):
        params = [self.cmd, "-mps", file]
        
        if self.timeout is not None:
            params += ["-timeout", str(self.timeout)]

        lpsolve = subprocess.Popen(params, stdout=subprocess.PIPE)

        out, err = lpsolve.communicate(b"")

        result = 0
        vars = []

        for line in out.decode().split("\n"):
            line = line.strip()

            match = self.value_re.match(line)
            if match:
                result = int(float(match.group(1)))

            match = self.var_re.match(line)
            if match:
                var = match.group(1)
                val = int(match.group(2))
                
                if val:
                    vars += [(var, val)]

        return (result, vars)


class Symphony:
    cmd = "symphony"
    var_re = re.compile(r"([a-z0-9]+) +([0-9.]+)")
    value_re = re.compile(r"Solution Cost: ([0-9.]+)")

    def __init__(self, timeout=None):
        self.timeout = timeout

    def solve_mps(self, file):
        params = [self.cmd, "-F", file]
        
        if self.timeout is not None:
            params += ["-time", str(self.timeout)]

        lpsolve = subprocess.Popen(params, stdout=subprocess.PIPE)

        out, err = lpsolve.communicate(b"")

        result = 0
        vars = []

        for line in out.decode().split("\n"):
            line = line.strip()

            # print(line)
            match = self.value_re.match(line)
            if match:
                result = int(float(match.group(1)))

            if not result:
                continue

            match = self.var_re.match(line)
            if match:
                var = match.group(1)
                val = int(float((match.group(2))))
                
                if val:
                    vars += [(var, val)]

        return (result, vars)

class Scip:
    cmd = "scip"
    var_re = re.compile(r"^([a-z0-9]+) +([0-9.]+)[ \t]+\(.*\)$")
    value_re = re.compile(r"^objective value: +([0-9.]+)$")

    def __init__(self, timeout=None):
        self.timeout = timeout

    def solve_mps(self, file):
        params = [self.cmd, "-f", file]
        
        if self.timeout is not None:
            limit = "limits/time = {}".format(self.timeout)
            settings = "setting.set"

            open(settings, "w").write(limit)

            params += ["-s", settings]

        lpsolve = subprocess.Popen(params, stdout=subprocess.PIPE)

        out, err = lpsolve.communicate(b"")

        result = 0
        vars = []

        for line in out.decode().split("\n"):
            line = line.strip()

            match = self.value_re.match(line)
            if match:
                result = int(float(match.group(1)))

            match = self.var_re.match(line)
            if match:
                var = match.group(1)
                val = int((match.group(2)))
                
                if val:
                    vars += [(var, val)]

        return (result, vars)


class Glpk:
    cmd = "glpsol"
    var_re = re.compile(r"[0-9]+ +([a-z0-9]+) +\* +([0-9.]+)")
    value_re = re.compile(r"Objective: +[A-Za-z0-9]+ = ([0-9.]+)")
    start_re = re.compile(r"No. +Column name +Activity +Lower bound +Upper bound")
    
    def __init__(self, timeout=None):
        self.timeout = timeout

    def solve_mps(self, file):
        params = [self.cmd, file, "-o", "glpk.out"]
        
        if self.timeout is not None:
            params += ["--tmlim", str(self.timeout)]

        lpsolve = subprocess.Popen(params, stdout=subprocess.PIPE)

        out, err = lpsolve.communicate(b"")

        result = 0
        vars = []

        seen_start = False

        out = open("glpk.out", "r").read()

        for line in out.split("\n"):
            line = line.strip()

            match = self.value_re.match(line)
            if match:
                result = int(float(match.group(1)))

            if self.start_re.match(line):
                seen_start = True

            if not seen_start:
                continue

            match = self.var_re.match(line)
            if match:
                var = match.group(1)
                val = int((match.group(2)))
                
                if val:
                    vars += [(var, val)]

        return (result, vars)


