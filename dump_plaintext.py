'''
`ropen` refers to an alias for `python view_and_maybe_edit.py`
'''

import utils
import sys


assert len(sys.argv) == 2, sys.argv[0] + ' takes exactly one argument'

utils.dump_plaintext(sys.argv[1])
