#!/usr/bin/ruby

require '/var/www/cgi-bin/constantvals'
require 'active_support/time'
require 'clockwork'
require 'logger'

include Clockwork
include ConstantValues

@logger = Logger.new("make_reception_list.log")

## 1分毎に新しい予約メールとキャンセルメールを確認する　##
every(1.minute, 'check_mail.job') {
  completeDocument = combineWithPhonenumber(getReceptionXML)
  writeReceptionListToDb(completeDocument)
  @logger.info("Re-genareted reception list")
}
