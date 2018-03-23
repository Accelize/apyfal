import os, sys
import logging
import acceleratorAPI

# Setup logging handlers
logging.getLogger('acceleratorAPI').setLevel(logging.INFO)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logging.getLogger().addHandler(console)


