#!/usr/bin/ruby

require 'nokogiri'
require 'rexml/document'
require 'faraday'
require 'logger'
require 'date'
require 'time'
require 'cgi'
require 'twilio-ruby'
require 'rubygems'
require 'sqlite3'
require '../constantvals'

include ConstantValues

# CGIパラメータ
cgi_data = CGI.new
unless cgi_data['smsto'].empty?
    tmp = cgi_data['smsto'].delete('-')
    SMSTO = "+81" + tmp[1..(tmp.length-1)]
else
    SMSTO = nil
end

## @logger設定
#@logger = Logger.new('./error.log')
#@reserve_logger = Logger.new('./reserve_error.log')

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

def writeReceptionListToDb(receptionXML)
    newPatientIDs = Array.new
    canceledPatientIDs = Array.new

    DB.transaction do 
        # 当日（TODAY）のORCA上の受付患者を収める一時テーブル（T_ORCA_RECEPTION）
        DB.execute('CREATE TEMPORARY TABLE T_ORCA_RECEPTION (
            Date text,
            AcceptanceID text,
            AcceptanceTime text,
            AppointmentTime text,
            OrdNo integer,
            ID_Patient text NOT NULL,
            NameKanji text,
            NameKana text,
            Sex text,
            Birthday text,
            Physician text,
            Phonenumber text
            );')

        receptionXML.xpath('//Acceptlst_Information_child').each do |patientInfo|
          newLine = [   
                        Date.today.strftime('%Y-%m-%d'),                # 今日の日付
                        patientInfo.at_xpath('Acceptance_Id').text,     # AcceptanceID
                        patientInfo.at_xpath('Acceptance_Time').text,   # AcceptanceTime
                        patientInfo.at_xpath('Appointment_Time').nil? ? '': patientInfo.at_xpath('Appointment_Time').text,  # AppointmentTime
                        '',                                             # OrdNo (後で割り付ける)
                        patientInfo.at_xpath('Patient_Information/Patient_ID').text,    # ID_Patient
                        patientInfo.at_xpath('Patient_Information/WholeName').text,     # NameKanji
                        patientInfo.at_xpath('Patient_Information/WholeName_inKana').text,           # NameKana
                        patientInfo.at_xpath('Patient_Information/Sex').text == '1' ? '男' : '女',    # Sex
                        patientInfo.at_xpath('Patient_Information/BirthDate').nil? ? '': patientInfo.at_xpath('Patient_Information/BirthDate').text,     # Birthday
                        patientInfo.at_xpath('Physician_WholeName').text,               # Physician
                        patientInfo.at_xpath('Patient_Information/PhoneNumber').nil? ? '': patientInfo.at_xpath('Patient_Information/PhoneNumber').text  # Phonenumber                                           # Phonenumber
                    ]
          DB.execute("INSERT INTO T_ORCA_RECEPTION VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", *newLine)
        end

        # 新規受付患者のIDリスト (newPatientIDs) 取得
        DB.execute('SELECT T_ORCA_RECEPTION.ID_Patient FROM T_ORCA_RECEPTION LEFT OUTER JOIN T_RECEPTION_TODAY
                    ON (T_ORCA_RECEPTION.ID_Patient = T_RECEPTION_TODAY.ID_Patient)
                    WHERE T_RECEPTION_TODAY.ID_Patient IS NULL
                    ORDER BY T_ORCA_RECEPTION.AcceptanceTime ASC').each do |id|
            newPatientIDs << id[0]
        end

        # 受付取り消し患者のIDリスト (canceledPatientIDs) 取得
        DB.execute('SELECT T_RECEPTION_TODAY.ID_Patient FROM T_RECEPTION_TODAY LEFT OUTER JOIN T_ORCA_RECEPTION
                    ON (T_RECEPTION_TODAY.ID_Patient = T_ORCA_RECEPTION.ID_Patient AND T_RECEPTION_TODAY.Date = T_ORCA_RECEPTION.Date)
                    WHERE T_ORCA_RECEPTION.ID_Patient is null').each do |id|
            canceledPatientIDs << id[0]
        end

        # 新規受付患者のT_RECEPTIONへの追加
        if !newPatientIDs.empty?
            lastOrdNo = DB.execute('SELECT MAX(OrdNo) FROM T_RECEPTION_TODAY')[0][0] 
            currentOrdNo = lastOrdNo.nil? ? 1 : lastOrdNo + 1

            newPatientIDs.each do |id|
                DB.execute("UPDATE T_ORCA_RECEPTION SET OrdNo = #{currentOrdNo} WHERE ID_Patient = \"#{id}\";")
                currentOrdNo += 1
            end

            # T_RECEPTIONに新規受付情報を追加
            DB.execute("INSERT INTO T_RECEPTION SELECT * FROM T_ORCA_RECEPTION WHERE T_ORCA_RECEPTION.ID_Patient IN (\"#{newPatientIDs.join('","')}\");")
        end

        # 受付取り消し患者のT_RECEPTIONからの削除
        if !canceledPatientIDs.empty?
            # T_RECEPTIONに新規受付情報を追加
            DB.execute("DELETE FROM T_RECEPTION WHERE T_RECEPTION.ID_Patient IN (\"#{canceledPatientIDs.join('","')}\");")
        end       

    end
end

def renderedHTML
    DB.results_as_hash = true
    acceptantPatients = DB.execute("SELECT * FROM T_RECEPTION_TODAY ORDER BY T_RECEPTION_TODAY.OrdNo ASC;")

    outHTML = Array.new

    ## HTMLヘッダー部分
    outHTML.push(<<-"TOHERE_HEADER")
<html lang="ja">
    <head>
      <title>受付患者一覧</title>
      <meta charset="utf-8" />
      <link rel="stylesheet" type="text/css" href="/reception.css" />
      <meta http-equiv="refresh" content="60" />
    </head> 
    
    <body>
      <h1>受付患者一覧</h1>
      <h3>受付日：#{Date.today.strftime("%Y-%m-%d")}</h3>
      <h3>更新時間：#{Time.now}（1分毎に自動更新）</h3>
    TOHERE_HEADER
    ## ここまで

    ## HTML表部分
    outHTML.push(<<-"TOHERE")
    <table id="acceptance-patients">
        <thead>
            <tr>
              <th>呼び出し順</th>
              <th>受付ID</th>
              <th>受付時間</th>
              <th>予約時間</th>
              <th>待ち時間</th>
              <th>患者番号</th>
              <th>氏名</th>
              <th>カナ</th>
              <th>性別</th>
              <th>生年月日</th>
              <th>主治医</th>
              <th>10分前<br />呼び出し</th>
            </tr>
        </thead>
        <tbody>
    TOHERE

    # 現在時刻を nowTime に格納
    t = Time.now
    nowTime = Time.local(2018, 11, 21, t.hour, t.min)

    acceptantPatients.each do |acceptantPatient|
        acceptantTime_min = acceptantPatient["AcceptanceTime"].match(/([0-9][0-9]):([0-9][0-9]):([0-9][0-9])/)[2]
        acceptantTime_hour = acceptantPatient["AcceptanceTime"].match(/([0-9][0-9]):([0-9][0-9]):([0-9][0-9])/)[1]
        acceptantTime = Time.local(2018, 11, 21, acceptantTime_hour, acceptantTime_min)
        waitingTime_hour = (nowTime - acceptantTime).to_i/60/60
        waitingTime_min  = (nowTime - acceptantTime).to_i/60%60
        
        if waitingTime_hour < 10
            waitingTime_hour_str = "0#{waitingTime_hour}"
        else
            waitingTime_hour_str = waitingTime_hour.to_s
        end

        if waitingTime_min < 10
            waitingTime_min_str = "0#{waitingTime_min}"
        else
            waitingTime_min_str = waitingTime_min.to_s
        end

        acceptantPatient["WaitingPeriod"] = "#{waitingTime_hour_str}:#{waitingTime_min_str}"

        outHTML.push(<<-"TOHERE")
            <tr patid="#{acceptantPatient["ID_Patient"]}">
            <td style="text-align: end;" class="rank">#{acceptantPatient["OrdNo"]}</td>
            <td>#{acceptantPatient["AcceptanceID"]}</td>
            <td>#{acceptantPatient["AcceptanceTime"]}</td>
            <td>#{acceptantPatient["AppointmentTime"]}</td>
            <td>#{acceptantPatient["WaitingPeriod"]}</td>
            <td>#{acceptantPatient["ID_Patient"]}</td>
            <td>#{acceptantPatient["NameKanji"]}</td>
            <td>#{acceptantPatient["NameKana"]}</td>
            <td>#{acceptantPatient["Sex"]}</td>
            <td>#{acceptantPatient["Birthday"]}</td>
            <td>#{acceptantPatient["Physician"]}</td>
            <td><a href="#{CGI_URI}?smsto=#{acceptantPatient["Phonenumber"]}" class="square_btn">Send SMS</a></td>
            </tr>
            TOHERE
    end

    outHTML.push(<<-"TOHERE")
        </tbody>
    </table>

    <script src="/jquery-3.3.1.min.js"></script>
    <script src="/jquery/external/jquery/jquery.js"></script>
    <script src="/jquery/jquery-ui.js"></script>
    <script type="text/javascript">
        startTimeout = function() {
            var reloadInterval = 60000;

            reloadTimer = setTimeout(
                    function() {location.reload(true)},
                    reloadInterval);
        }

        $(function() {
          $('#acceptance-patients tbody').disableSelection();
          $('#acceptance-patients tbody').sortable({
               cursor: 'move',
               opacity: 0.5,
               update: function(){
                 var ajax = $.ajax({
                      type: 'POST',
                      url: '#{DBUPDATE_URI}',
                      data: { patientids: $(this).sortable("toArray", {attribute: "patid"}).join(",")}
                 });

                 ajax.fail(function( XMLHttpRequest, textStatus, errorThrown ) {
                    alert( "XMLHttpRequest : " + XMLHttpRequest.status + "; textStatus     : " + textStatus + "; errorThrown    : " + errorThrown.message );
                  });

                  var rows = $('#acceptance-patients .rank');
                  for (var i = 0, rowTotal = rows.length; i < rowTotal; i += 1) {
                      $($(".rank")[i]).text(i + 1);
                  }

                }
          })
        })
    </script>
    </body>
    </html>
    TOHERE

    return outHTML.join

end

if SMSTO.nil?
    ## ローカルテスト
    #file = File.open('output.xml')
    #getReceptionXML = Nokogiri::XML(file)
    #completeDocument = getReceptionXML
    completeDocument = combineWithPhonenumber(getReceptionXML)
    writeReceptionListToDb(completeDocument)

    print "Content-type: text/html\n\n"
    print renderedHTML
else
    TwilioClient.messages.create(
        from: SMSFROM,
        to: SMSTO,
        body: "あと10分で診察可能です．クリニックにお戻りください．"
    )

    sentMessageHtml = <<"EOF"
<html>
<head>
    <meta charset="utf-8">
    <title>送信完了</title>
    <link rel="stylesheet" type="text/css" href="/style.css"/>
</head>

<body>
    <h1>案内メールを送信しました</h1>

    <a href="http://192.168.0.3/cgi-bin/receptionlist.cgi" class="square_btn">受付一覧に戻る</a>
</body>
</html>
EOF
    
    print "Content-type: text/html\n\n"
    print sentMessageHtml
end