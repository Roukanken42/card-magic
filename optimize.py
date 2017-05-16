import argparse
import solver
import fetcher

solvers = {
    "gurobi": solver.Gurobi(),
    "glpk": solver.Glpk(),
    "lp_solve": solver.Lp_solve(),
    "symphony": solver.Symphony(),
    "scip": solver.Scip(),
}


parser = argparse.ArgumentParser()
parser.add_argument("cards", nargs="*", type=str, help="Cards to buy and their quantities in format: [Amount] [Card name]")
parser.add_argument("-s", "--solver", nargs="?", type=str, choices=solvers.keys(), help="Solver to use for optimizing")
parser.add_argument("-t", "--timelimit", type=int, nargs="?", help="Timelimit for solving ILP problem")
parser.add_argument("-c", "--country", type=str, nargs="?", help="Country to which are cards shipped")
parser.add_argument("-f", "--file", type=str, nargs="?", help="Read amount and card names from file")
parser.add_argument("-wmps", type=str, nargs="?", help="Write the mps problem to file")

args = parser.parse_args()

it = iter(args.cards)
args.cards = [(card, int(amount)) for amount, card in zip(it, it)]

args.country = "SK" if not args.country else args.country
args.wmps = "temp.mps" if not args.wmps else args.wmps

if args.file:
    cards = []
    for line in open(args.file):
        amount, card = line.strip().split(maxsplit=1)
        cards += [(card, int(amount))]

    args.cards = cards

if args.timelimit:
    solvers = {
        "gurobi": solver.Gurobi(),
        "glpk": solver.Glpk(timeout=args.timelimit),
        "lp_solve": solver.Lp_solve(timeout=args.timelimit),
        "symphony": solver.Symphony(timeout=args.timelimit),
        "scip": solver.Scip(timeout=args.timelimit),
    }


# print(args.cards)

print("Buying: ")
for card, amount in args.cards:
    print("  ", str(amount) + "x", "   ", card)

print()

if not args.solver:
    args.solver = "symphony"

print("With", args.solver)
print()

fetcher.solve(args.cards, country=args.country, lpsolver=solvers[args.solver], file=args.wmps)