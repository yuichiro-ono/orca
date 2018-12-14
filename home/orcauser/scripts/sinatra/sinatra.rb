require 'sinatra'
require 'sinatra/reloader'
require 'sinatra/cross_origin'
require 'sqlite3'
require 'rubygems'
require 'date'

DB_FILE = "/var/www/cgi-bin/reception/reception.db".freeze
DB = SQLite3::Database.new(DB_FILE)
 
set :environment, :production

configure do
  enable :cross_origin
end

before do
  response.headers['Access-Control-Allow-Origin'] = '*'
end

options "*" do
  response.headers["Allow"] = "HEAD,GET,PUT,POST,DELETE,OPTIONS"
  response.headers["Access-Control-Allow-Headers"] = "X-Requested-With, X-HTTP-Method-Override, Content-Type, Cache-Control, Accept"
  response.headers["Access-Control-Allow-Origin"] = "*"
  200
end

post '/ordno' do 
	patientIds = params["patientids"].split(',')
	date = Date.today.strftime('%Y-%m-%d')

#	"#{orderNos} #{patientIds}"
#	"UPDATE T_RECEPTION SET OrdNo = #{orderNos[0]} WHERE (ID_Patient = \"#{patientIds[0]}\" And Date = \"#{date}\");"

	DB.exec('BEGIN;')
	for i in 0..(patientIds.length-1) do
		DB.exec("UPDATE T_RECEPTION SET OrdNo = #{i + 1} WHERE (ID_Patient = '#{patientIds[i]}' And Date = '#{date}');")
	end
 	DB.exec('COMMIT;')

end

post '/wtst' do 
	patientId = params["patientid"]
	if params["newstatus"] == "診察待ち"
		newStatus = 0
	elsif params["newstatus"] == "診察中断"
		newStatus = 1
	else 
		newStatus = 2
	end

	date = Date.today.strftime('%Y-%m-%d')

#	"#{orderNos} #{patientIds}"
#	"UPDATE T_RECEPTION SET OrdNo = #{orderNos[0]} WHERE (ID_Patient = \"#{patientIds[0]}\" And Date = \"#{date}\");"

	DB.exec("UPDATE t_reception SET waitingstatus = #{newStatus} WHERE (ID_Patient = '#{patientId}' And Date = '#{date}');")
end

get '/' do
    "Hello World!"
end