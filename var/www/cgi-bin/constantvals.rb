require 'rexml/document'
require 'sqlite3'
require 'twilio-ruby'
require 'faraday'

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
	DBUPDATE_URI = 'http://192.168.0.3:4567/post'

	# XML Formatter
	Formatter = REXML::Formatters::Default.new

	# Twilio
	ACCOUNT_SID = 'AC5d3e2fc87350647170f448c942b154f0'.freeze
	AUTH_TOKEN = 'c04996dd3bbf4f3ecb63903f7187144b'.freeze
	TwilioClient = Twilio::REST::Client.new(ACCOUNT_SID, AUTH_TOKEN)
	SMSFROM = '+18503785426'.freeze # Your Twilio number

	# DB
	DB_FILE = "/var/www/cgi-bin/reception/reception.db".freeze
	DB = SQLite3::Database.new(DB_FILE)

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

end
