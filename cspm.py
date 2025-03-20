#!/usr/local/bin/python3.13
import os
from main import CSPM


def lambda_handler(event, context):
    CSPM().main()


if __name__ == "__main__":
    if not os.getenv("LAMBDA", False):
        CSPM().main()
