require 'faye/websocket'
require 'eventmachine'
require 'json'
require 'logger'
require 'securerandom'
require '/var/www/cgi-bin/constantvals'

include ConstantValues

HOME_DIR = '/home/orcauser/scripts/printacceptnum'

@logger = Logger.new("#{HOME_DIR}/print_acceptnum.log")

def printAcceptanceNumber(body_hash)
  system("python printToThermprt.py #{body_hash["Accept_Id"]} #{body_hash["Accept_Date"]} #{body_hash["Accept_Time"]}")
end

EM.run {
  ws = Faye::WebSocket::Client.new('ws://192.168.0.3:9400/ws', [], :headers => {'X-GINBEE-TENANT-ID' => '1'})

  subId = ''
  # ORCA PUSH APIへのリクエストID
  req_id  = "PatientAcceptReq_#{Time.now}"

  # ORCA PUSH APIへのリクエスト
  req_str = <<EOS
{
"command" : "subscribe",
"req.id" : "#{req_id}", 
"event" : "patient_accept" 
}
EOS

  ws.on :open do |event|
    p [:open]

    # patient_accept (新規患者受付)イベントをリクエストする．
    ws.send(req_str)
  end

  ws.on :message do |event|
    p [:message, event.data]
    res_hash= JSON.parse(event.data)

    if res_hash["command"] == 'subscribed'
      @logger.info("Patient_accept request was subscribed.")
      subId = res_hash["sub.id"]
    elsif res_hash["command"] == 'event'
      data_hash = res_hash["data"]
      body_hash = data_hash["body"]
      @logger.debug(body_hash["Patient_Mode"])
      body_hash["uuid"] = SecureRandom.uuid

      if (res_hash["sub.id"] == subId && body_hash["Patient_Mode"] == "add" && data_hash["event"] == "patient_accept")
        printAcceptanceNumber(body_hash)
        completeDocument = combineWithPhonenumber(getReceptionXML)
        updateReceptionListAll(completeDocument)
        exportDataToHeroku
      end
    end

  end

  ws.on :close do |event|
    p [:close, event.code, event.reason]
    ws = nil
  end
}