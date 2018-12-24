#!/usr/bin/ruby

require '/var/www/cgi-bin/constantvals'
require 'active_support/time'
require 'clockwork'
require 'logger'

include Clockwork
include ConstantValues

@logger = Logger.new("make_reception_list.log")

## 1分毎に新しい受付を確認する　##
every(1.minute, 'make_reception.job') {
  completeDocument = combineWithPhonenumber(getReceptionXML)
  updateReceptionListAll(completeDocument)
  @logger.info("Updated reception list.")
}
