require 'date'
require 'pg'

# TIME_FOR_ONE_PATIENT: 患者1人あたり所要時間(min)
TIME_FOR_ONE_PATIENT = 7

# DB
DB_HOST = 'ec2-54-163-245-64.compute-1.amazonaws.com'.freeze
DB_NAME = 'd6190mj636qia0'.freeze
DB_USER = 'ikezymvynmeniz'.freeze
DB_PASSWD = '63078f2a-887d-4699-920f-e51636e399d8'.freeze
DB = PG::Connection.new(:host => DB_HOST, :dbname => DB_NAME, :user => DB_USER, :password => DB_PASSWD, :sslmode => 'require')
DB.internal_encoding = "UTF-8"

DB.exec("select * from t_export;")
DB.disconnect
