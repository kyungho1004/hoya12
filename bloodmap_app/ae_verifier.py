import importlib.util
spec = importlib.util.spec_from_file_location('drug_db','drug_db.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
db = {}
m.ensure_onco_drug_db(db)
by_alias = {}
missing = []
for k,v in db.items():
    alias = (v or {}).get('alias') or k
    ae = (v or {}).get('ae','').strip()
    if alias not in by_alias or len(ae)>len(by_alias[alias]['ae']):
        by_alias[alias] = {'key':k,'alias':alias,'ae':ae}
for alias, rec in by_alias.items():
    if (not rec['ae']) or ('부작용 정보 필요' in rec['ae']):
        missing.append(rec)
print('Unique alias count:', len(by_alias))
print('Placeholders remaining:', len(missing))
if missing:
    print('Sample missing:', missing[:10])
else:
    print('All good.')
