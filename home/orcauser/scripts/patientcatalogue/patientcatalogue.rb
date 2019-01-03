require '/var/www/cgi-bin/constantvals'
require 'logger'
require 'romkan'
require 'nkf'
#require 'clockwork'
#require 'active_support/time'

#include Clockwork
include ConstantValues

class PatientCatalogue
  SCRIPT_HOME = '/home/orcauser/scripts/patientcatalogue'.freeze
  PATIENT_CATOLOGUE_DIR = "/home/public/PatientCatalogue".freeze
  @logger = Logger.new("#{SCRIPT_HOME}/patient_catalogue.log")

  def self.makeAllPatientCatalog
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
      pat_romaName = NKF.nkf("--hiragana -w -Z1", pat_kanaName).to_roma.upcase
      pat_hankanaName = NKF.nkf('-w -x -Z1 -Z4', pat_kanaName)
      pat_birthday = patientInfo.at_xpath('BirthDate').text.gsub(/-/, '')
      pat_sex      = patientInfo.at_xpath('Sex').text == '1' ? 'M' : 'F'

      # File.open(PATIENT_CATOLOGUE_DIR + '/' + pat_id.to_s, 'w') do |f|
      #   f.puts("(0010,0010) PN [#{pat_romaName}]")
      #   f.puts("(0010,0020) LO [#{pat_id}]")
      #   f.puts("(0010,0030) DA [#{pat_birthday}]")
      #   f.puts("(0010,0040) CS [#{pat_sex}]")
      # end

      # 患者情報をCSVに出力（１患者(ID)１ファイル）
      File.open(PATIENT_CATOLOGUE_DIR + '/' + pat_id.to_s + '.csv', 'w:SJIS:UTF-8') do |f|
        f.puts("#{pat_id},#{pat_kanjiName},#{pat_hankanaName},#{pat_romaName},#{pat_sex},#{pat_birthday}")
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

  def self.makeIndividualPatientCatalog(patient_id)
    @logger.info("OK")
    begin
      response = connectionToORCA.post do |req| 
        req.url '/api01rv2/patientlst2v2', {:class => '01'}
        req.headers['Content-type'] = 'application/xml'

        xml = <<"EOS"
<data>
        <patientlst2req type="record">
                <Patient_ID_Information type="array">
                        <Patient_ID_Information_child type="record">
                                <Patient_ID type="string">#{patient_id}</Patient_ID>
                        </Patient_ID_Information_child>
                </Patient_ID_Information>
        </patientlst2req>
</data>
EOS
        req.body = xml
      end
    rescue Exception => e
      @logger.error(e)
    end

    res_xml = Nokogiri::XML(response.body)
    @logger.info(res_xml)

    if res_xml.at_xpath('//Api_Result').text != '00' 
      @logger.error('Failed to get patient catalogue')
      exit
    elsif res_xml.at_xpath('//Target_Patient_Count').text == '0000'
      @logger.error('No patient is registered.')    
      exit
    elsif res_xml.at_xpath('//WholeName').text == '患者番号がありません'
         @logger.error('No patient is registered.')    
      exit
    end

    res_xml.xpath('//Patient_Information_child').each do |patientInfo|
      pat_id = patientInfo.at_xpath('Patient_ID').text
      pat_kanjiName = patientInfo.at_xpath('WholeName').text
      pat_kanaName = patientInfo.at_xpath('WholeName_inKana').text
      pat_romaName = NKF.nkf("--hiragana -w -Z1", pat_kanaName).to_roma.upcase
      pat_hankanaName = NKF.nkf('-w -x -Z4 -Z1', pat_kanaName)
      pat_birthday = patientInfo.at_xpath('BirthDate').text.gsub(/-/, '')
      pat_sex      = patientInfo.at_xpath('Sex').text == '1' ? 'M' : 'F'

      # File.open(PATIENT_CATOLOGUE_DIR + '/' + pat_id.to_s, 'w') do |f|
      #   f.puts("(0010,0010) PN [#{pat_romaName}]")
      #   f.puts("(0010,0020) LO [#{pat_id}]")
      #   f.puts("(0010,0030) DA [#{pat_birthday}]")
      #   f.puts("(0010,0040) CS [#{pat_sex}]")
      # end

      # 患者情報をCSVに出力（１患者(ID)１ファイル）
      File.open(PATIENT_CATOLOGUE_DIR + '/' + pat_id.to_s + '.csv', 'w:SJIS:UTF-8') do |f|
        f.puts("#{pat_id},#{pat_kanjiName},#{pat_hankanaName},#{pat_romaName},#{pat_sex},#{pat_birthday}")
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
end


### 定期的に患者カタログを更新するのを中止 ###
## 4時間毎に患者カタログを作成する　##
#every(4.hours, 'making_patient_catalogue.job') {
#  PatientCatalogue.makeAllPatientCatalog
#  puts 'Made patient catalogue.'
#}

if ARGV[0] == '--update-all'
  PatientCatalogue.makeAllPatientCatalog
  puts 'Made patient catalogue.'
end
