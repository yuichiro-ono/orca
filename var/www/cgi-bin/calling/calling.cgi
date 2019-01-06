#!/usr/bin/ruby

require 'nokogiri'
require 'rexml/document'
require 'date'
require 'cgi'
require 'rubygems'
require '../constantvals'

include ConstantValues

# 患者1人あたりの平均診察時間（単位：分）
TIME_FOR_ONE_PATIENT = 7

def renderedHTML
  acceptantPatients = DB.exec('select * from t_reception_today where (waitingstatus = 0) order by order_no ASC;')
  query_waiting_people = DB.exec("select count(*) from t_reception_today where (waitingstatus = 0);")
  waiting_people = 0
  waiting_time = 0

    if query_waiting_people.ntuples > 0
      waiting_people = query_waiting_people.getvalue(0,0).to_i - 1
      waiting_time = TIME_FOR_ONE_PATIENT * waiting_people
    end

  outHTML = Array.new

  outHTML.push(<<-"TOHERE")
    <html>
    <head>
      <meta charset="utf-8" />
      <title>待ち状況</title>
      <link rel="stylesheet" href="/calling.css" />
      <meta http-equiv="refresh" content="60" />
    </head>
    <body>
      <video id="bg-video" src="/video/bg.mp4" autoplay loop></video>
      <div id="site-box">
        <div class="title">■現在の待ち状況</div>
        <div class="time"><p id="RealtimeClockArea"><img class="clock" src="/images/clock.png" alt="現在の時刻は"> </p></div>
        <div class="next">
  TOHERE

  if acceptantPatients.to_a.empty?
    outHTML.push(<<-"TOHERE")
          <h2>現在受付中の方はおられません</h2>
        </div>
    TOHERE
  else
    outHTML.push(<<-"TOHERE")
          <h2 class="label_next_patient">以下の番号の方は診察室にお入りください </h2>

          <table class="next_patient_box">
            <tr>
              <td class="number_cell_next">#{acceptantPatients[0]["acceptance_id"]}</td>
            </tr>
          </table>

          <h4 class="label_waiting_people">ただいまの受付人数</h4>
          <div class="content_waiting_people">#{waiting_people} 人</div>
          <h4 class="label_waiting_time">ただいまの待ち時間</h4>
          <div class="content_waiting_time">#{waiting_time} 分</div>
        </div>
    TOHERE
  end

  if acceptantPatients.to_a.length >= 2
      outHTML.push(<<-"TOHERE")
      <div class="other">
        <h2 class="label_other_patient">以下の受付番号の方はしばらくお待ちください</h2>
        <table class="still_not_called_numbers_table">
          <tr>
      TOHERE

      acceptantPatients.to_a.slice(2..4).each do |patient|
        outHTML.push(<<-"TOHERE")
            <td class="number_cell_other">#{patient["acceptance_id"]}</td>
          TOHERE
      end

      outHTML.push("</tr>\n")
        
      if acceptantPatients.to_a.length >= 5
        outHTML.push("<tr>\n")
        acceptantPatients.to_a.slice(5..7).each do |patient|
          outHTML.push(<<-"TOHERE")
              <td class="number_cell_other">#{patient["acceptance_id"]}</td>
            TOHERE
        end
        outHTML.push("</tr>\n")

        if acceptantPatients.to_a.length >= 8
          outHTML.push("<tr>\n")
          acceptantPatients.to_a.slice(8..10).each do |patient|
            outHTML.push(<<-"TOHERE")
                <td class="number_cell_other">#{patient["acceptance_id"]}</td>
              TOHERE
          end
          outHTML.push("</tr>\n")
        end
      end

      outHTML.push(<<-"TOHERE")
      </table>
      </div>
      TOHERE
  end
  
  outHTML.push(<<-"TOHERE")
      <div class="footer">
      更新時間 #{Time.now.strftime("%k:%M")}
      </div>
    </div>
    
    <script>
      function set2fig(num) {
         // 桁数が1桁だったら先頭に0を加えて2桁に調整する
         var ret;
         if( num < 10 ) { ret = "0" + num; }
         else { ret = num; }
         return ret;
      }
      function showClock2() {
         var nowTime = new Date();
         var nowHour = set2fig( nowTime.getHours() );
         var nowMin  = set2fig( nowTime.getMinutes() );
         var nowSec  = set2fig( nowTime.getSeconds() );
         var msg = '<img class="clock" src="/images/clock.png" alt="現在の時刻は">' + nowHour + ":" + nowMin;
         document.getElementById("RealtimeClockArea").innerHTML = msg;
      }
      setInterval('showClock2()',1000);
    </script>
  </body>
  </html>
  TOHERE

  return outHTML.join
end

# CGIパラメータ
#cgi_data = CGI.new

print "Content-type: text/html\n\n"
print renderedHTML
