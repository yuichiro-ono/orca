#!/usr/bin/ruby

require 'nokogiri'
require 'rexml/document'
require 'date'
require 'cgi'
require 'rubygems'
require '../constantvals'

include ConstantValues

def renderedHTML
  acceptantPatients = DB.exec('SELECT * FROM t_reception_today ORDER BY t_reception_today.order_no ASC;')

  outHTML = Array.new

  outHTML.push(<<-"TOHERE")
    <html>
    <head>
      <meta charset="utf-8" />
      <title>呼び出しリスト</title>
      <link rel="stylesheet" href="/calling.css" />
      <meta http-equiv="refresh" content="60" />
    </head>
    <body>
      <div id="site-box">
        <div class="title">診察順番案内</div>
        <div class="next">
  TOHERE

  if acceptantPatients.result_status == PG::Result.PGRES_EMPTY_QUERY
    outHTML.push(<<-"TOHERE")
          <div class="subtitle">現在受付中の方はおられません</div>
        </div>
    TOHERE
  else
    outHTML.push(<<-"TOHERE")
        <div class="subtitle">
          次の受付番号の方は間もなく診察です
        </div>
        <br style="clear:left;" />
        <table class="frame">
          <tr>
            <td>
              <table class="numbers_next">
                <tr>
                  <td class="number_cell_next">#{acceptantPatients["acceptance_id"]}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        </div>
    TOHERE

    if acceptantPatients.length >= 2
      outHTML.push(<<-"TOHERE")
      <div class="other">
        <div class="subtitle">
          以下の受付番号の方はしばらくお待ちください
        </div>
        <br style="clear:left;" />
        <table class="frame">
          <tr>
    TOHERE

      acceptantPatients.slice(1..3).each do |patient|
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

      <div class="footer">
      更新時間 #{Time.now.strftime("%k:%M")}
      </div>
    </div>
  </body>
  </html>
      TOHERE
    end
  end

  return outHTML.join
end

# CGIパラメータ
#cgi_data = CGI.new

print "Content-type: text/html\n\n"
print renderedHTML
