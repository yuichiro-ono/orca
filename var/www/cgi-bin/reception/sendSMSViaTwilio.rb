# Download the twilio-ruby library from twilio.com/docs/libraries/ruby
require 'twilio-ruby'

account_sid = 'AC5d3e2fc87350647170f448c942b154f0'
auth_token = 'c04996dd3bbf4f3ecb63903f7187144b'
client = Twilio::REST::Client.new(account_sid, auth_token)

from = '+18503785426' # Your Twilio number
to = '+819019686476' # Your mobile phone number

client.messages.create(
from: from,
to: to,
body: "Hey friend!"
)
