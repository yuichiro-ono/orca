require '/var/www/cgi-bin/constantvals'
require 'logger'
require 'romkan'
require 'nkf'
require 'clockwork'
require 'active_support/time'
require 'logger'

include Clockwork
include ConstantValues

SCRIPT_HOME = '/home/orcauser/scripts/patientcatalogue'.freeze
PATIENT_CATOLOGUE_DIR = "/home/public/PatientCatalogue".freeze
LOCKFILE = "#{SCRIPT_HOME}/pid".freeze

@logger = Logger.new("#{SCRIPT_HOME}/patient_catalogue.log")

def file_check
   # ファイルチェック
   if File.exist?(LOCKFILE)
      # pidのチェック
      pid = 0
      File.open(LOCKFILE, "r"){|f|
         pid = f.read.chomp!.to_i
      }
      if exist_process(pid)
         $logger.info("The process has already started.")
         exit
      else
         $logger.error("プロセス途中で死んでファイル残ったままっぽいっす")
         exit
      end
   else
   # なければLOCKファイル作成
      File.open(LOCKFILE, "w"){|f|
         # LOCK_NBのフラグもつける。もしぶつかったとしてもすぐにやめさせる。
         locked = f.flock(File::LOCK_EX | File::LOCK_NB)
         if locked
            f.puts $$
         else
            $logger.error("lock failed -> pid: #{$$}")
         end
      }
   end
end
 
# プロセスの生き死に確認
def exist_process(pid)
   begin
      gid = Process.getpgid(pid)
      return true
   rescue => ex
      puts ex
      return false
   end
end

def main
  file_check

  begin
    response = connectionToORCA.post do |req| 
      req.url '/api01rv2/patientlst1v2', {:class => '01'}
      req.headers['Content-type'] = 'application/xml'

      xml = <<"EOS"
<data>
    <patientlst1req type="record">
            <Base_StartDate type="string">2018-08-01</Base_StartDate>
            <Contain_TestPatient_Flag type="string">1</Contain_TestPatient_Flag>
    </patientlst1req>
</data>
EOS
      req.body = xml
    end
  rescue Exception => e
    @logger.error(e)
  end

  res_xml = Nokogiri::XML(response.body)

  if res_xml.at_xpath('//Api_Result').text != '00' 
    @logger.error('Failed to get patient catalogue')
    exit
  elsif res_xml.at_xpath('//Target_Patient_Count').text == '0000'
    @logger.error('No patient is registered.')    
    exit
  end

  res_xml.xpath('//Patient_Information_child').each do |patientInfo|
    pat_id = patientInfo.at_xpath('Patient_ID').text
    pat_kanjiName = patientInfo.at_xpath('WholeName').text
    pat_kanaName = patientInfo.at_xpath('WholeName_inKana').text
    pat_romaName = NKF.nkf("--hiragana -w", pat_kanaName).to_roma.upcase
    pat_romaName = pat_romaName.sub(/([A-Z]+)　([A-Z]+)/, '\2^\1')
    pat_birthday = patientInfo.at_xpath('BirthDate').text.gsub(/-/, '')
    pat_sex      = patientInfo.at_xpath('Sex').text == '1' ? 'M' : 'F'

    # File.open(PATIENT_CATOLOGUE_DIR + '/' + pat_id.to_s, 'w') do |f|
    #   f.puts("(0010,0010) PN [#{pat_romaName}]")
    #   f.puts("(0010,0020) LO [#{pat_id}]")
    #   f.puts("(0010,0030) DA [#{pat_birthday}]")
    #   f.puts("(0010,0040) CS [#{pat_sex}]")
    # end

    File.open(PATIENT_CATOLOGUE_DIR + '/' + pat_id.to_s, 'w:SJIS:UTF-8') do |f|
      f.puts("#{pat_id}\t#{pat_kanjiName}\t\t#{pat_romaName}\t#{pat_sex}\t#{pat_birthday}")
    end

    @logger.info('Made patient catalogue.')
  end

  ## PATIENT_CATOLOGUE_DIR にあるdumpファイルをDICOMデータに変換
  # Dir.chdir(PATIENT_CATOLOGUE_DIR)
  # Dir.open PATIENT_CATOLOGUE_DIR do |dir|
  #   dir.each do |file|
  #     `dump2dcm +te -q #{file} ../#{file}.wl`
  #   end
  # end
end

## 10分毎に患者カタログを作成する　##
every(5.minutes, 'making_patient_catalogue.job') {
  main
  puts 'Made patient catalogue.'
}

