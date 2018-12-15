require '/var/www/cgi-bin/constantvals'
require 'clockwork'

include Clockwork
include ConstantValues

## 10分毎に患者カタログを作成する　##
every(5.minutes, 'export_reception_list_to_heroku.job') {
  exportDataToHeroku
}

