#!/usr/bin/ruby

require '/var/www/cgi-bin/constantvals'
require 'clockwork'

include Clockwork
include ConstantValues


## 1分毎に新しい予約メールとキャンセルメールを確認する　##
every(1.minute, 'check_mail.job') {
  completeDocument = combineWithPhonenumber(getReceptionXML)
  writeReceptionListToDb(completeDocument)
}
