# -*- coding: utf-8 -*-
try:
    from bloodmap.app import main
except Exception:
    # If the folder was renamed to bloodmap_app
    from bloodmap_app.app import main

if __name__ == "__main__":
    main()
