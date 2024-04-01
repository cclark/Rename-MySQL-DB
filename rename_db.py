#!/usr/bin/env python

# The MIT License
#
# Copyright (c) 2010 Chuck Clark <cclark@ziclix.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
rename_db.py
A simple script to provide rename/mv like functionality for MySQL databases.

"""
import logging
import sys
from optparse import OptionParser
import MySQLdb as mysql

def rename_db(old_db, new_db, options=None):
  conn_props = {}
  if options.user:
    conn_props["user"] = options.user
  if options.password:
    conn_props["passwd"] = options.password
  if options.host:
    conn_props["host"] = options.host
  cur = None
  try:
    cur = mysql.connect(**conn_props).cursor()
    if not exec_sql(cur, "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '%s'" % (old_db)):
      logging.error("DB %s does not exist" % (old_db))
      return -1
    if not exec_sql(cur, "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '%s'" % (new_db)):
      if options.create_database:
        exec_sql(cur, "CREATE DATABASE %s" % (new_db))
      else:
        logging.error("DB %s does not exist." % (old_db))
        return -2
    trigger_count = exec_sql(cur, "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = '%s'" % (old_db))
    logging.info("Found %s triggers" % (trigger_count))
    if trigger_count:
      for trigger in cur.fetchall():
        if options.drop_triggers:
          exec_sql(cur, "DROP TRIGGER %s.%s;" % (old_db, trigger[0]))
        else:
          logging.error("Unable to perform rename because of trigger %s.%s" % (old_db, trigger[0]))
          return -3
    table_count = exec_sql(cur, "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '%s'" % (old_db))
    logging.info("Found %s tables" % (table_count))
    if not table_count:
      logging.info("Check to make sure you provided valid login credentials if you expected tables to exist in this database")
    else: 
      for table in cur.fetchall():
        exec_sql(cur, "RENAME TABLE %s.%s TO %s.%s" % (old_db, table[0], new_db, table[0]))
  except mysql._mysql.OperationalError as e:
    logging.error(e)
  finally:
    if cur:
      cur.close()

def exec_sql(cur, sql):
  logging.debug(sql)
  return cur.execute(sql)
  
def main():
  usage = """usage: %prog [options] <olddb> <newdb>
  Script to 'rename' a MySQL database by moving all tables from one database to another.
"""
  
  parser = OptionParser(usage=usage, version="%prog 0.1")
  parser.add_option("--host", dest="host",
                    help="Host address of mysql server")
  parser.add_option("-p", "--password", dest="password",
                    help="Password for mysql user")
  parser.add_option("-u", "--user", dest="user",
                    help="User name for mysql")
  parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                    help="Be verbose and show debugging level output")
  parser.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False,
                    help="Be quiet.  Show no output unless an error occurs")
  parser.add_option("--drop-triggers", dest="drop_triggers", action="store_true", default=False,
                    help="Drop triggers instead of listing triggers preventing the renames from occurring")
  parser.add_option("--create-database", dest="create_database", action="store_true", default=False,
                    help="Create the destination database if it doesn't exist")
  
  options, args = parser.parse_args()
  if len(args) != 2:
    parser.error("Must specify an existing old db with tables to be moved to an existing empty db.  Try --help for usage details.")
    
  if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
  elif options.quiet:
    logging.basicConfig(level=logging.ERROR)
  else:
    logging.basicConfig(level=logging.INFO)

  old_db, new_db = args

  return rename_db(old_db, new_db, options)
  
if __name__ == '__main__':  
  sys.exit(main())
