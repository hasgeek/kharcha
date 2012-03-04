import sys
import os
import os.path
sys.path.insert(0, os.path.dirname(__file__))
os.environ['ENVIRONMENT'] = 'production'
from kharcha import app as application
