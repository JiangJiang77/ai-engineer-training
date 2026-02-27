#!/usr/bin/env python3
import sys

if __name__ == "__main__":
    numbers = [int(x) for x in sys.argv[1:]]
    print(sum(numbers))
