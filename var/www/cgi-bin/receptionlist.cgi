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
require './constantvals'

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

def isSelected(option_index, option_value)
    if option_index.to_i == option_value.to_i
        return 'selected'
    else
        return 'error'
    end
end

def renderedHTML
    acceptantPatients = DB.exec("SELECT * FROM t_reception_today ORDER BY t_reception_today.order_no ASC;")

    outHTML = Array.new

    ## HTMLヘッダー部分
    outHTML.push(<<-"TOHERE_HEADER")
<html lang="ja">
    <head>
      <title>受付患者一覧</title>
      <meta charset="utf-8" />
      <link rel="stylesheet" type="text/css" href="/reception.css" />
      <link rel="stylesheet" type="text/css" href="/jquery-ui.css" />
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
              <th>呼出番号</th>
              <th>受付時間</th>
              <th>予約時間</th>
              <th>待ち時間</th>
              <th>患者番号</th>
              <th>氏名</th>
              <th>カナ</th>
              <th>性別</th>
              <th>生年月日</th>
              <th>主治医</th>
              <th>状態</th>
              <th>10分前<br />呼び出し</th>
              <th>呼出番号シート</th>
            </tr>
        </thead>
        <tbody>
    TOHERE

    # 現在時刻を nowTime に格納
    t = Time.now
    nowTime = Time.local(2018, 11, 21, t.hour, t.min)

    # 診察状態
    waiting_status = ['診察待ち', '診察中・中断', '診察終了']

    acceptantPatients.each do |acceptantPatient|
        acceptantTime_min = acceptantPatient["acceptance_time"].match(/([0-9][0-9]):([0-9][0-9]):([0-9][0-9])/)[2]
        acceptantTime_hour = acceptantPatient["acceptance_time"].match(/([0-9][0-9]):([0-9][0-9]):([0-9][0-9])/)[1]
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

        acceptantPatient["waitingperiod"] = "#{waitingTime_hour_str}:#{waitingTime_min_str}"

        outHTML.push(<<-"TOHERE")
            <tr patid="#{acceptantPatient["patient_id"]}">
            <td style="text-align: end;" class="rank">#{acceptantPatient["order_no"]}</td>
            <td>#{acceptantPatient["acceptance_id"]}</td>
            <td>#{acceptantPatient["acceptance_time"]}</td>
            <td>#{acceptantPatient["appointment_time"]}</td>
            <td>#{acceptantPatient["waitingperiod"]}</td>
            <td>#{acceptantPatient["patient_id"]}</td>
            <td>#{acceptantPatient["namekanji"]}</td>
            <td>#{acceptantPatient["namekana"]}</td>
            <td>#{acceptantPatient["sex"]}</td>
            <td>#{acceptantPatient["birthday"]}</td>
            <td>#{acceptantPatient["physician"]}</td>
            <td>
                <select class="waiting_status" patid="#{acceptantPatient["patient_id"]}">
                    <option value="診察待ち" #{isSelected(0,acceptantPatient['waitingstatus'])}>診察待ち</option>
                    <option value="診察中" #{isSelected(1,acceptantPatient['waitingstatus'])}>診察中・診察中断</option>
                    <option value="診察終了" #{isSelected(2,acceptantPatient['waitingstatus'])}>診察終了</option>
                </select>
            </td>
            <td><a href="#{CGI_URI}?smsto=#{acceptantPatient["Phonenumber"]}" class="square_btn">Send SMS</a></td>
            <td><button class="re_issue_acceptnumber" acceptid="#{acceptantPatient["acceptance_id"]}" accepttime="#{acceptantPatient["acceptance_time"]}">再発行</button></td>
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
                      url: '#{DBUPDATE_ORDERNO_URI}',
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
          });

          $('.waiting_status').change(function() {
                 var ajax = $.ajax({
                      type: 'POST',
                      url: '#{DBUPDATE_WAITINGSTATUS_URI}',
                      data: { patientid: $(this).attr('patid'), newstatus: $(this).val() }
                 });

                 ajax.fail(function( XMLHttpRequest, textStatus, errorThrown ) {
                    alert( "XMLHttpRequest : " + XMLHttpRequest.status + "; textStatus     : " + textStatus + "; errorThrown    : " + errorThrown.message );
                  });

          }); 

          $('.re_issue_acceptnumber').click(function() {
                 var ajax = $.ajax({
                      type: 'POST',
                      url: '#{DBUPDATE_REISSUE_URI}',
                      data: { acceptid: $(this).attr('acceptid'), accepttime: $(this).attr('accepttime')}
                 });

                 ajax.fail(function( XMLHttpRequest, textStatus, errorThrown ) {
                    alert( "XMLHttpRequest : " + XMLHttpRequest.status + "; textStatus     : " + textStatus + "; errorThrown    : " + errorThrown.message );
                  });

          }); 
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
    updateReceptionListAll(completeDocument)

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