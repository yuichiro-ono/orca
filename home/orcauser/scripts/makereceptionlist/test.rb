require 'pg'

begin
	DB = PG::connect(:host => "localhost", :user => "orcauser", :password => "orca", :dbname => "reception_db")
	DB.internal_encoding = "UTF-8"
rescue PG::ConnectionBad => e
end

DB.exec("BEGIN;")
# 新規受付患者のT_RECEPTIONへの追加
    lastOrdNo = DB.exec("select max(order_no) from t_reception_today;").getvalue(0,0)
    puts lastOrdNo
    currentOrdNo = lastOrdNo.nil? ? 1 : lastOrdNo + 1
DB.exec("COMMIT;")