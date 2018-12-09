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
  File.open('updateOrderNo.pid', 'w') {|f| f.write Process.pid }
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

post '/post' do 
	patientIds = params["patientids"].split(',')
	date = Date.today.strftime('%Y-%m-%d')

#	"#{orderNos} #{patientIds}"
#	"UPDATE T_RECEPTION SET OrdNo = #{orderNos[0]} WHERE (ID_Patient = \"#{patientIds[0]}\" And Date = \"#{date}\");"

	DB.transaction do
		for i in 0..(patientIds.length-1) do
			DB.execute("UPDATE T_RECEPTION SET OrdNo = #{i + 1} WHERE (ID_Patient = '#{patientIds[i]}' And Date = '#{date}');")
		end
 	end

end

get '/wait/:acceptid' do |id|
	@acceptID = id
	erb :wait
end

get '/' do
    "Hello World!"
end