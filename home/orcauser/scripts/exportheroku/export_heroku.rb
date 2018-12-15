require '/var/www/cgi-bin/constantvals'
require 'clockwork'
require 'active_support/time'
require 'logger'

include Clockwork
include ConstantValues

logger = logger.new("export_heroku.log")

## 10分毎に患者カタログを作成する　##
every(5.minutes, 'export_reception_list_to_heroku.job') {
  exportDataToHeroku
  logger.info('Sent reception date to heroku!')
}

