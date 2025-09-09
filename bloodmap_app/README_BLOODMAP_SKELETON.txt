BloodMap Skeleton (0909)
------------------------
Generated minimal skeleton for data/ and utils/ so that:
- `from utils import user_key, init_state` works
- basic lab interpretation functions exist
- pediatric antipyretic dose calculator exists
- food guidance & ANC low hygiene tips included
- drug tables include APL -> MTX & 6-MP

Move/keep this folder as your `bloodmap_app/` package.
Ensure your app.py uses these modules:
  from utils import user_key, init_state
  from utils.interpret import interpret_labs
  from utils.reports import build_markdown_report

Also rename 'fonfs' -> 'fonts' in your repo and place NanumGothic TTFs inside.
