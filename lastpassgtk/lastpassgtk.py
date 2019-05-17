#!/usr/bin/env python3

import sys
from lastpassgtk import LastPassGTK

def main():
    app = LastPassGTK()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
