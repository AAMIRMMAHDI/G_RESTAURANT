from kavenegar import *
api = KavenegarAPI('58423059794D3734465A6A777777642F507076446D67344D63664970466F486C386B2F3854504F6A575A303D')
params = { 'sender' : '2000660110', 'receptor': '09934135235', 'message' :'کد تاییدی ما 225خوبی' }
response = api.sms_send(params)