import pymongo
import datetime

def pytest_funcarg__db(request):
    """return a database object"""
    conn = pymongo.Connection()
    db = conn.mongoquery_testdatabase
    return db

