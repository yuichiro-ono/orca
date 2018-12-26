require 'faye/websocket'
require 'eventmachine'
require 'json'
require 'logger'
require '/var/www/cgi-bin/constantvals'
require '/home/orcauser/scripts/patientcatalogue/patientcatalogue'

PatientCatalogue.makeIndividualPatientCatalog("00002")