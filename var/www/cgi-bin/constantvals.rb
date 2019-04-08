require 'rexml/document'
require 'twilio-ruby'
require 'faraday'
require 'pg'
require 'securerandom'
require 'logger'

module ConstantValues

	# ORCanswer_API関連
	DEPARTMENT_CODE = '01'.freeze   # 診療科コード
	PHYSICIAN_CODE  = '10000'.freeze       # ドクターコード．現在は固定．人が増えたら，拡張する．
	APPOINTMENT_INFORMATION = '01'  # 予約内容区分（01:患者による予約、 02:医師による予約）
	ORCanswer_USER ='ormaster'.freeze
	ORCanswer_PASSWD = 'ormaster'.freeze

	# Test URL
	ORCA_URI = 'http://localhost:8000/'.freeze
	CGI_URI = '/cgi-bin/receptionlist/receptionlist.cgi'
	DBUPDATE_ORDERNO_URI = 'http://localhost:4567/ordno'
	DBUPDATE_WAITINGSTATUS_URI = 'http://localhost:4567/wtst'
    DBUPDATE_REISSUE_URI = 'http://localhost:4567/reissue'

	# XML Formatter
	Formatter = REXML::Formatters::Default.new

	# Twilio
	ACCOUNT_SID = 'AC5d3e2fc87350647170f448c942b154f0'.freeze
	AUTH_TOKEN = 'c04996dd3bbf4f3ecb63903f7187144b'.freeze
	TwilioClient = Twilio::REST::Client.new(ACCOUNT_SID, AUTH_TOKEN)
	SMSFROM = '+18503785426'.freeze # Your Twilio number

    # Other
    SCRIPT_DIR = '/var/www/cgi-bin'

	# DB
	begin
		DB = PG::connect(:host => "localhost", :user => "orcauser", :password => "orca", :dbname => "reception_db")
		DB.internal_encoding = "UTF-8"
	rescue PG::ConnectionBad => e
		
	end

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

	def updateReceptionListAll(receptionXML)
	    newPatientIDs = Array.new
	    canceledPatientIDs = Array.new

        # 当日（TODAY）のORCA上の受付患者を収める一時テーブル（T_ORCA_RECEPTION）
        begin
            DB.exec('DROP TABLE t_orca_reception;')
        rescue PG::Error => e
        end

        DB.exec('BEGIN;') 
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
            waitingstatus integer,
            uuid text
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
                        0,
                        SecureRandom.uuid
                    ]
          DB.exec("INSERT INTO t_orca_reception VALUES (\'#{newLine.join("\', \'")}\');")
        end

        # 新規受付患者のIDリスト (newPatientIDs) 取得
        DB.exec('SELECT t_orca_reception.patient_id FROM t_orca_reception LEFT OUTER JOIN t_reception_today
                    ON (t_orca_reception.patient_id = t_reception_today.patient_id)
                    WHERE t_reception_today.patient_id IS NULL
                    ORDER BY t_orca_reception.acceptance_time ASC;').each do |id|
            newPatientIDs << id["patient_id"]
        end

        # 受付取り消し患者のIDリスト (canceledPatientIDs) 取得
        DB.exec('SELECT t_reception_today.patient_id FROM t_reception_today LEFT OUTER JOIN t_orca_reception
                    ON (t_reception_today.patient_id = T_ORCA_RECEPTION.patient_id AND t_reception_today.acceptance_date = t_orca_reception.acceptance_date)
                    WHERE t_orca_reception.patient_id is null;').each do |id|
            canceledPatientIDs << id["patient_id"]
        end
        DB.exec('COMMIT;') 

        DB.exec("BEGIN;")
        # 新規受付患者のT_RECEPTIONへの追加
        if !newPatientIDs.empty?
            lastOrdNo = DB.exec("select max(order_no) from t_reception_today;").getvalue(0,0)
            p lastOrdNo
            currentOrdNo = lastOrdNo.nil? ? 1 : lastOrdNo.to_i + 1

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
#    	begin 
	        DB.exec('DROP TABLE t_export;')
    	    DB.exec("CREATE TABLE t_export AS SELECT acceptance_date, acceptance_id, acceptance_time, order_no, waitingstatus, uuid from t_reception_today;")
	    	system('pg_dump --no-acl --no-owner -h localhost -U orcauser -t t_export reception_db > /var/tmp/export.dump')
            if !$?.success?
            end

	        system('heroku pg:reset -a wait-1210 --confirm wait-1210')
            if !$?.success?
            end

	        system('heroku pg:psql -a wait-1210 < /var/tmp/export.dump')
            if !$?.success?
            end

	        system('rm /var/tmp/export.dump')
#    	rescue Exception => e 
#    		@logger.error(e)
#    	end
    end

    ## 受付一覧をXMLで取得する．
    def getReceptionXML
        req_xml = REXML::Document.new
        req_xml << REXML::XMLDecl.new('1.0', 'UTF-8')
        # ルートノードを作成
        root = REXML::Element.new('data')
        req_xml.add_element(root)

        # ルートノードの下に子ノードを追加
        xml_acceptlstreq = REXML::Element.new('acceptlstreq')
        xml_acceptlstreq.add_attribute('type', 'record')
        root.add_element(xml_acceptlstreq)
        xml_acceptance_date = REXML::Element.new('Acceptance_Date')
        xml_acceptance_date.add_attribute('type', 'string')
        xml_acceptance_date.add_text(Date.today.strftime("%Y-%m-%d"))
        root.add_element(xml_acceptance_date)
        xml_department_code = REXML::Element.new('Department_Code')
        xml_department_code.add_attribute('type', 'string')
        xml_department_code.add_text(DEPARTMENT_CODE)
        root.add_element(xml_department_code)
        xml_physician_code = REXML::Element.new('Physician_Code')
        xml_physician_code.add_attribute('type', 'string')
        xml_physician_code.add_text(PHYSICIAN_CODE)
        root.add_element(xml_physician_code)

        begin
          reception_response = connectionToORCA.post do |req| 
            req.url '/api01rv2/acceptlstv2', {:class => '01'}
            req.headers['Content-type'] = 'application/xml'

            xml = ''
            Formatter.write(req_xml.root, xml)
            req.body = xml
          end
        rescue Exception => e
          #@logger.error(e)
        end

        return reception_response
    end

    def getPhonenumber(ids)
        phonenums = Hash.new
        
        req_xml = REXML::Document.new
        req_xml << REXML::XMLDecl.new('1.0', 'UTF-8')
        # ルートノードを作成
        root = REXML::Element.new('data')
        req_xml.add_element(root)

        # ルートノードの下に子ノードを追加
        xml_patientlst2req = REXML::Element.new('patientlst2req')
        xml_patientlst2req.add_attribute('type', 'record')
        root.add_element(xml_patientlst2req)
        xml_patient_id_information = REXML::Element.new('Patient_ID_Information')
        xml_patient_id_information.add_attribute('type', 'array')
        xml_patientlst2req.add_element(xml_patient_id_information)

        ids.each do |id|
            xml_patient_id_information_child = REXML::Element.new('Patient_ID_Information_child')
            xml_patient_id_information_child.add_attribute('type', 'record')
            xml_patient_id_information.add(xml_patient_id_information_child)

            xml_patient_id = REXML::Element.new('Patient_ID')
            xml_patient_id.add_attribute('type', 'string')
            xml_patient_id.add_text(id)
            xml_patient_id_information_child.add(xml_patient_id)        
        end

        begin
          phonenums_response = connectionToORCA.post do |req| 
            req.url '/api01rv2/patientlst2v2', {:class => '01'}
            req.headers['Content-type'] = 'application/xml'

            xml = ''
            Formatter.write(req_xml.root, xml)
            req.body = xml
          end
        rescue Exception => e
          #@logger.error(e)
        end

        res_xml = Nokogiri::XML(phonenums_response.body)

        res_xml.xpath('//Patient_ID').each do |patientIdNode|
            id = patientIdNode.text
            phonenum1 = patientIdNode.at_xpath('../Home_Address_Information/PhoneNumber1').text unless patientIdNode.at_xpath('../Home_Address_Information/PhoneNumber1').nil?
            phonenum2 = patientIdNode.at_xpath('../Home_Address_Information/PhoneNumber2').text unless patientIdNode.at_xpath('../Home_Address_Information/PhoneNumber2').nil?
            if !phonenum1.nil? && (phonenum1.start_with?('090') || phonenum1.start_with?('080') ||phonenum1.start_with?('070'))
                phonenums[id.to_sym] = phonenum1
            elsif !phonenum2.nil? && (phonenum2.start_with?('090') || phonenum2.start_with?('080') ||phonenum2.start_with?('070'))
                phonenums[id.to_sym] = phonenum2
            end
        end

        return phonenums
    end

    def combineWithPhonenumber(receptionXML)
        document = Nokogiri::XML(receptionXML.body)

        ids = Array.new()
        document.xpath('//Patient_ID').each do |patientIdNode|
            ids << patientIdNode.text
        end

        phonenums = getPhonenumber(ids)

        document.xpath('//Patient_ID').each do |patientIdNode|
            id = patientIdNode.text
            phonenumberNode = Nokogiri::XML::Node.new('PhoneNumber', document)
            phonenumberNode.content = phonenums[id.to_sym]
            phonenumberNode['type'] = 'string'
            patientIdNode.add_next_sibling(phonenumberNode) 
        end

        return document

    end

end
