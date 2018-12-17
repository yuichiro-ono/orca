require 'rexml/document'
require 'twilio-ruby'
require 'faraday'
require 'pg'

module ConstantValues

	# ORCanswer_API関連
	DEPARTMENT_CODE = '01'.freeze   # 診療科コード
	PHYSICIAN_CODE  = '10000'.freeze       # ドクターコード．現在は固定．人が増えたら，拡張する．
	APPOINTMENT_INFORMATION = '01'  # 予約内容区分（01:患者による予約、 02:医師による予約）
	ORCanswer_USER ='ormaster'.freeze
	ORCanswer_PASSWD = 'orcamaster'.freeze

	# Test URL
	ORCA_URI = 'http://localhost:8000/'.freeze
	CGI_URI = '/cgi-bin/receptionlist/receptionlist.cgi'
	DBUPDATE_ORDERNO_URI = 'http://192.168.0.3:4567/ordno'
	DBUPDATE_WAITINGSTATUS_URI = 'http://192.168.0.3:4567/wtst'
    DBUPDATE_REISSUE_URI = 'http://192.168.0.3:4567/reissue'

	# XML Formatter
	Formatter = REXML::Formatters::Default.new

	# Twilio
	ACCOUNT_SID = 'AC5d3e2fc87350647170f448c942b154f0'.freeze
	AUTH_TOKEN = 'c04996dd3bbf4f3ecb63903f7187144b'.freeze
	TwilioClient = Twilio::REST::Client.new(ACCOUNT_SID, AUTH_TOKEN)
	SMSFROM = '+18503785426'.freeze # Your Twilio number

	# DB
	DB = PG::connect(:host => "localhost", :user => "orcauser", :password => "orca", :dbname => "reception_db")
	DB.internal_encoding = "UTF-8"

	def connectionToORCA
	  # ORCAへのConnection作成
	  conn = Faraday.new(:url => ORCA_URI) do |builder|
	    builder.request :url_encoded  ## URLをエンコードする
	    builder.request :retry, max: 2, interval: 0.05
	    ## ログを標準出力に出したい時(本番はコメントアウトでいいかも)
	    #builder.use Faraday::Response::Logger
	    #builder.response :@logger  ## エラー対応
	    builder.response :raise_error
	    builder.use Faraday::Request::BasicAuthentication, ORCanswer_USER, ORCanswer_PASSWD  ## Basic認証する
	    builder.adapter :net_http  ## アダプター選択（選択肢は他にもあり）
	  end
	  return conn
	end

	def writeReceptionListToDb(receptionXML)
	    newPatientIDs = Array.new
	    canceledPatientIDs = Array.new

	    DB.exec('BEGIN;') 
        # 当日（TODAY）のORCA上の受付患者を収める一時テーブル（T_ORCA_RECEPTION）
        DB.exec('CREATE TEMPORARY TABLE t_orca_reception (
            acceptance_date date,
            acceptance_id text,
            acceptance_time time,
            appointment_time time,
            order_no integer,
            patient_id text not null,
            namekanji text,
            namekana text,
            sex text,
            birthday text,
            physician text,
            phonenumber text,
            waitingstatus integer
            );')

        receptionXML.xpath('//Acceptlst_Information_child').each do |patientInfo|
          newLine = [   
                        Date.today.strftime('%Y-%m-%d'),                # 今日の日付
                        patientInfo.at_xpath('Acceptance_Id').text,     # AcceptanceID
                        patientInfo.at_xpath('Acceptance_Time').text,   # AcceptanceTime
                        patientInfo.at_xpath('Appointment_Time').nil? ? '00:00:00': patientInfo.at_xpath('Appointment_Time').text,  # AppointmentTime
                        0,                                             # OrdNo (後で割り付ける)
                        patientInfo.at_xpath('Patient_Information/Patient_ID').text,    # ID_Patient
                        patientInfo.at_xpath('Patient_Information/WholeName').text,     # NameKanji
                        patientInfo.at_xpath('Patient_Information/WholeName_inKana').text,           # NameKana
                        patientInfo.at_xpath('Patient_Information/Sex').text == '1' ? '男' : '女',    # Sex
                        patientInfo.at_xpath('Patient_Information/BirthDate').nil? ? 'null': patientInfo.at_xpath('Patient_Information/BirthDate').text,     # Birthday
                        patientInfo.at_xpath('Physician_WholeName').text,               # Physician
                        patientInfo.at_xpath('Patient_Information/PhoneNumber').nil? ? 'null': patientInfo.at_xpath('Patient_Information/PhoneNumber').text,  # Phonenumber
                        0
                    ]
          DB.exec("INSERT INTO t_orca_reception VALUES (\'#{newLine.join("\', \'")}\');")
        end

        # 新規受付患者のIDリスト (newPatientIDs) 取得
        DB.exec('SELECT t_orca_reception.patient_id FROM t_orca_reception LEFT OUTER JOIN t_reception_today
                    ON (t_orca_reception.patient_id = t_reception_today.patient_id)
                    WHERE t_reception_today.patient_id IS NULL
                    ORDER BY t_orca_reception.acceptance_time ASC').each do |id|
            newPatientIDs << id["patient_id"]
        end

        # 受付取り消し患者のIDリスト (canceledPatientIDs) 取得
        DB.exec('SELECT t_reception_today.patient_id FROM t_reception_today LEFT OUTER JOIN t_orca_reception
                    ON (t_reception_today.patient_id = T_ORCA_RECEPTION.patient_id AND t_reception_today.acceptance_date = t_orca_reception.acceptance_date)
                    WHERE t_orca_reception.patient_id is null').each do |id|
            canceledPatientIDs << id["patient_id"]
        end

        # 新規受付患者のT_RECEPTIONへの追加
        if !newPatientIDs.empty?
            lastOrdNo = DB.exec('SELECT MAX(Order_no) FROM t_reception_today')[0][0] 
            currentOrdNo = lastOrdNo.nil? ? 1 : lastOrdNo + 1

            newPatientIDs.each do |id|
                DB.exec("UPDATE t_orca_reception SET order_no = #{currentOrdNo} WHERE (patient_id = \'#{id}\');")
                currentOrdNo += 1
            end

            # T_RECEPTIONに新規受付情報を追加
            newPatientIDs.each do |id| 
	            DB.exec("INSERT INTO t_reception SELECT * FROM t_orca_reception WHERE (t_orca_reception.patient_id = \'#{id}\');")
	      	end
        end

        # 受付取り消し患者のT_RECEPTIONからの削除
        if !canceledPatientIDs.empty?
            # T_RECEPTIONに新規受付情報を追加
            DB.exec("DELETE FROM t_reception WHERE t_reception.patient_id IN (\'#{canceledPatientIDs.join("\', \'")}\');")
        end       

        DB.exec('COMMIT;')
	end

    def exportDataToHeroku
        DB.exec('DROP TABLE t_export;')
        DB.exec("CREATE TABLE t_export AS SELECT acceptance_date, acceptance_id, acceptance_time, order_no, waitingstatus from t_reception_today;")
        system('pg_dump --no-acl --no-owner -h localhost -U orcauser -t t_export reception_db > /var/tmp/export.dump')
        system('heroku config:get DATABASE_URL -a wait-1210')
        system('DATABASE_URL=$(heroku config:get DATABASE_URL --app wait-1210) heroku pg:reset DATABASE -a wait-1210 -c wait-1210')
        system('heroku pg:psql -a wait-1210 < /var/tmp/export.dump')
        system('rm /var/tmp/export.dump')
    end

end
