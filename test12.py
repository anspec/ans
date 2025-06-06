from num2words import num2words
import json

def handle(data):
 try:
  d = json.loads(data)
  num = d["number"]
  if num:
    n = int(num)
    prop = num2words(n,lang='ru')
    d["prop"] = prop
    d["status"] = '1'
  else:
    d["prop"] = ""
    d["status"] = '0'
 except:
  data["status"] = 'False'
  data["prop"] = ""

 return d

dat = '{"number":"88888"}'
d = handle(dat)
if d['status']=='1':
  print(f"Без ошибок {d['prop']}")
else:
  print(f"Ошибка {d}")