require 'faye/websocket'
require 'eventmachine'
require 'json'
require 'logger'
require 'securerandom'
require '/var/www/cgi-bin/constantvals'
require '/home/u1_ax/scripts/patientcatalogue/patientcatalogue'

include ConstantValues

HOME_DIR = '/home/u1_ax/scripts/printacceptnum'

@logger = Logger.new("#{HOME_DIR}/print_acceptnum.log")

def printAcceptanceNumber(body_hash)
  system("python printToThermprt.py #{body_hash["Accept_Id"]} #{body_hash["Accept_Date"]} #{body_hash["Accept_Time"]}")
end

def newPatientAcceptRequestStr(id)
  # ORCA PUSH APIへのリクエスト
  patientaccept_req_str = <<EOS
{
"command" : "subscribe",
"req.id" : "#{id}", 
"event" : "patient_accept" 
}
EOS

  return patientaccept_req_str
end

def newPatientInfoRequestStr(id)
  patientinfo_req_str = <<EOS  
{
"command" : "subscribe",
"req.id" : "#{id}", 
"event" : "patient_infomation" 
}
EOS
  return patientinfo_req_str
end

def start_connection
  ws = Faye::WebSocket::Client.new('ws://192.168.0.81:9400/ws', [], :headers => {'X-GINBEE-TENANT-ID' => '1'}, ping: 60)

  subId = Hash.new
  # ORCA PUSH APIへのリクエストID
  patientaccept_req_id = "PatientAcceptReq_#{Time.now}"
  patientinfo_req_id = "PatientInfoReq_#{Time.now}"

  patientaccept_req_str  = newPatientAcceptRequestStr(patientaccept_req_id)
  patientinfo_req_str = newPatientInfoRequestStr(patientinfo_req_id)

  ws.on :open do |event|
    p [:open]

    # patient_accept (新規患者受付)イベントとpatient_information（患者情報）イベントをリクエストする．
    ws.send(patientaccept_req_str)
    ws.send(patientinfo_req_str)
  end

  ws.on :message do |event|
    p [:message, event.data]
    res_hash= JSON.parse(event.data)

    if res_hash["command"] == 'subscribed'
      if res_hash["req.id"] == patientaccept_req_id 
        subId[:patientaccept] = res_hash["sub.id"]
        @logger.info("Patient accept event subscription id is #{subId[:patientaccept]}.")
      elsif res_hash["req.id"] == patientinfo_req_id 
        subId[:patientinfo] = res_hash["sub.id"]
        @logger.info("Patient information event subscription id is #{subId[:patientinfo]}.")
      end
    elsif res_hash["command"] == 'event'
      data_hash = res_hash["data"]
      body_hash = data_hash["body"]
      @logger.debug("#{res_hash}")

      if data_hash["event"] == "patient_accept" && res_hash["sub.id"] == subId[:patientaccept]
        body_hash["uuid"] = SecureRandom.uuid

        # 新規受付時に作動（受付情報変更時は作動しない）
        if body_hash["Patient_Mode"] == "add" || body_hash["Patient_Mode"] == "delete"
          @logger.info("Patient accept/delete event has occurred. ")

          # ラベル印刷
          printAcceptanceNumber(body_hash) if body_hash["Patient_Mode"] == "add" 
          
          completeDocument = combineWithPhonenumber(getReceptionXML)
          updateReceptionListAll(completeDocument)
          #exportDataToHeroku
        end
      elsif data_hash["event"] == "patient_infomation" && res_hash["sub.id"] == subId[:patientinfo]
        # 患者情報　追加 or 変更 時に作動
        if body_hash["Patient_Mode"] == "add" || body_hash["Patient_Mode"] == "modify"
          print body_hash["Patient_ID"]
          PatientCatalogue.makeIndividualPatientCatalog(body_hash["Patient_ID"])
        elsif body_hash["Patient_Mode"] == "del"
          PatientCatalogue.deleteIndividualPatientCatalog(body_hash["Patient_ID"])
        end

      end
    end
  end

  ws.on :close do |event|
    p [:close, event.code, event.reason]
    
    start_connection
  end
end

EM.run {
  start_connection
}