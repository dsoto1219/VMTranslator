import argparse


parser = argparse.ArgumentParser(prog="test_parser")
parser.add_argument("inputs", nargs='+')
args = parser.parse_args()

args.inputs = ["1", "2", "3"]

print(args.inputs)