#!/usr/bin/ruby

require 'nokogiri'
require 'rexml/document'
require 'date'
require 'cgi'
require 'rubygems'
require '../constantvals'

include ConstantValues

def renderedHTML
  acceptantPatients = DB.exec('SELECT * FROM t_reception_today WHERE (waitingstatus = 0) ORDER BY order_no ASC;')

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
          <div class="subtitle">現在受付中の方はおられません</div>
        </div>
    TOHERE
  else
    outHTML.push(<<-"TOHERE")
          <h2>
            以下の番号の方は診察室にお入りください
          </h2>
          <table class="numbers_next_box">
            <tr>
              <td class="number_cell_next">#{acceptantPatients[0]["acceptance_id"]}</td>
            </tr>
          </table>
        </div>
    TOHERE

    if acceptantPatients.to_a.length >= 2
      outHTML.push(<<-"TOHERE")
      <div class="other">
        <div class="subtitle">
          以下の受付番号の方はしばらくお待ちください
        </div>
        <br style="clear:left;" />
        <table class="frame">
          <tr>
    TOHERE

      acceptantPatients.to_a.slice(1..4).each do |patient|
        outHTML.push(<<-"TOHERE")
          <td>
            <table class="numbers_other">
              <tr><td class="number_cell_other">#{patient["acceptance_id"]}</td></tr>
            </table>
          </td>
          TOHERE
      end

      outHTML.push(<<-"TOHERE")
        </tr>
      </table>
      </div>
      TOHERE
    end
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
