# Oncology DB Patch (20251026_103506)

이 패치는 동일 스키마의 8개 약물을 서버에 바로 반영할 수 있도록 **3가지 배포 형식**을 제공합니다.

## 포함 약물 (keys)
venetoclax, gilteritinib, midostaurin, ivosidenib, enasidenib, glasdegib, azacitidine, decitabine

## 공통 스키마
key, names[], class, indications[], common_AEs[], emergent_flags[], contra[], dose_notes, ddi[], tips[], monitor{baseline[], during[], extra[]}

### 모니터 라벨 표준화
- Glucose: 공복혈당/당화혈색소
- Lipids: 지질프로필
- LFT: 간기능(AST/ALT, bilirubin)
- ILD: 간질성폐질환 관련 여부(필요 약물에 한해 명시)
- Renal/Electrolytes 등 서브라벨 포함

## 배포 옵션

### 1) RFC6902 JSON Patch
파일: `onc_patch_rfc6902.json`  
엔드포인트가 JSON Patch를 지원하면 그대로 업로드하세요. 각 op는 `/drugs/<key>` 경로에 **add(upsert)**로 구성되어 있습니다.

### 2) MongoDB (mongoimport)
파일: `onc_patch_mongo.ndjson`  
예시:
```
mongoimport --db yourdb --collection onc_drugs --mode upsert --upsertFields _id --file onc_patch_mongo.ndjson --jsonArray=false
```

### 3) PostgreSQL
파일: `onc_patch_postgres.sql`  
예시:
```
psql $DATABASE_URL -f onc_patch_postgres.sql
```
가정: `onc_drugs(key text primary key, data jsonb)` 구조.

---

## 검증 체크
- 필수 필드 누락 없음
- monitor 섹션의 라벨: Glucose, Lipids, LFT, (필요 시) ECG/Electrolytes/ILD 등 가독성 한글 병기
- emergent_flags/분화증후군/TLS/QT 워크플로 키워드 포함

문의 없이 바로 적용 가능하지만, 테이블/컬렉션명이 다르면 스크립트 상단 주석을 참고해 조정하세요.
