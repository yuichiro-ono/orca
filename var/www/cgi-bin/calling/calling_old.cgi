#!/usr/bin/ruby

require 'nokogiri'
require 'rexml/document'
require 'faraday'
require 'date'
require 'cgi'
require 'twilio-ruby'

# ORCanswer_API関連
DEPARTMENT_CODE = '01'.freeze   # 診療科コード
PHYSICIAN_CODE  = '10000'.freeze       # ドクターコード．現在は固定．人が増えたら，拡張する．
APPOINTMENT_INFORMATION = '01'  # 予約内容区分（01:患者による予約、 02:医師による予約）
ORCanswer_USER ='ormaster'.freeze
ORCanswer_PASSWD = 'orcamaster'.freeze

# Test URL
ORCA_URI = 'http://localhost:8000/'.freeze

# XML Formatter
Formatter = REXML::Formatters::Default.new

# CGIパラメータ
#cgi_data = CGI.new

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

completeDocument = Nokogiri::XML(getReceptionXML.body)
print completeDocument

if completeDocument.at_xpath('//Api_Result').text == '21' 
    # 受付患者がいないとき
    template = Nokogiri::XSLT(File.read('calling_empty.xslt'))
else
    # 受付患者がいるとき　
    template = Nokogiri::XSLT(File.read('calling.xslt'))
end

transformed_document = template.transform(completeDocument)

print "Content-type: text/html\n\n"
print transformed_document
